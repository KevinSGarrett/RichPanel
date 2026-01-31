from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

from richpanel_middleware.automation.llm_routing import get_confidence_threshold
from richpanel_middleware.automation.pii_sanitizer import sanitize_for_openai
from richpanel_middleware.automation.order_status_prompts import (
    build_order_status_intent_prompt,
)
from richpanel_middleware.commerce.order_lookup import _match_order_number_from_text
from richpanel_middleware.integrations.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    OpenAIClient,
    OpenAIRequestError,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_ORDER_STATUS_INTENT_MODEL") or os.environ.get(
    "OPENAI_MODEL", "gpt-5.2-chat-latest"
)
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 256
MAX_REASON_CHARS = 200

OPENAI_INTENT_ENABLED_DEFAULT = False
OPENAI_SHADOW_ENABLED_DEFAULT = False


def _fingerprint(value: str, *, length: int = 12) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_openai_intent_enabled() -> bool:
    return _env_flag(
        "MW_OPENAI_INTENT_ENABLED", default=OPENAI_INTENT_ENABLED_DEFAULT
    )


def get_openai_shadow_enabled() -> bool:
    return _env_flag(
        "MW_OPENAI_SHADOW_ENABLED", default=OPENAI_SHADOW_ENABLED_DEFAULT
    )


def _extract_json_object(content: str) -> Optional[str]:
    start = content.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(content)):
        char = content[idx]
        if in_string:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == "\"":
                in_string = False
            continue
        if char == "\"":
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : idx + 1]
    return None


def _coerce_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
    return None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text or None


def _normalize_language(value: Any) -> Optional[str]:
    text = _normalize_optional_text(value)
    if not text:
        return None
    if len(text) > 12:
        text = text[:12]
    return text.lower()


def _normalize_order_number(value: Any) -> Optional[str]:
    text = _normalize_optional_text(value)
    if not text:
        return None
    normalized = text.lstrip("#")
    if normalized.lower() in {"null", "none"}:
        return None
    return normalized or None


def extract_order_number_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    normalized = text.replace(",", "")
    order_number, _ = _match_order_number_from_text(normalized)
    if order_number:
        return order_number
    return None


def redact_ticket_text(text: str, *, max_chars: int = 280) -> Optional[str]:
    if not text:
        return None
    redacted = sanitize_for_openai(text, max_chars=max_chars)
    return redacted or None


@dataclass
class OrderStatusIntentResult:
    is_order_status: bool
    confidence: float
    reason: str
    extracted_order_number: Optional[str]
    language: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrderStatusIntentArtifact:
    result: Optional[OrderStatusIntentResult]
    llm_called: bool
    model: str
    response_id: Optional[str]
    response_id_unavailable_reason: Optional[str]
    confidence_threshold: float
    accepted: bool
    parse_error: Optional[str] = None
    gated_reason: Optional[str] = None
    prompt_fingerprint: str = ""
    ticket_excerpt_redacted: Optional[str] = None
    ticket_excerpt_fingerprint: Optional[str] = None
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["result"] = (
            self.result.to_dict() if isinstance(self.result, OrderStatusIntentResult) else None
        )
        return payload


def parse_intent_result(
    raw_text: str, *, fallback_text: Optional[str] = None
) -> Tuple[Optional[OrderStatusIntentResult], Optional[str]]:
    if not raw_text:
        return None, "empty_response"
    content = raw_text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if fence:
        content = fence.group(1).strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        extracted = _extract_json_object(content)
        if not extracted:
            return None, "invalid_json"
        try:
            parsed = json.loads(extracted)
        except json.JSONDecodeError:
            return None, "invalid_json"

    if not isinstance(parsed, dict):
        return None, "not_a_dict"

    is_order_status = _coerce_bool(parsed.get("is_order_status"))
    confidence = _coerce_float(parsed.get("confidence"))
    reason = _normalize_optional_text(parsed.get("reason")) or ""
    extracted_order_number = _normalize_order_number(parsed.get("extracted_order_number"))
    language = _normalize_language(parsed.get("language"))

    if is_order_status is None:
        return None, "missing_is_order_status"
    if confidence is None:
        return None, "missing_confidence"
    if not 0.0 <= confidence <= 1.0:
        return None, "confidence_out_of_range"

    if not extracted_order_number and fallback_text:
        extracted_order_number = extract_order_number_from_text(fallback_text)

    reason = reason[:MAX_REASON_CHARS]
    return (
        OrderStatusIntentResult(
            is_order_status=is_order_status,
            confidence=confidence,
            reason=reason,
            extracted_order_number=extracted_order_number,
            language=language,
        ),
        None,
    )


def _intent_gating_check(
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
) -> Optional[str]:
    if not get_openai_intent_enabled():
        return "openai_intent_disabled"
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
    if not allow_network:
        return "network_disabled"
    return None


def _prompt_fingerprint(model: str, message_count: int, user_length: int) -> str:
    payload = {
        "model": model,
        "message_count": message_count,
        "user_length": user_length,
    }
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()[:16]


def _response_id_info(
    response: Optional[ChatCompletionResponse],
) -> Tuple[Optional[str], Optional[str]]:
    if response is None:
        return None, "no_response"
    has_raw = isinstance(response.raw, dict)
    raw = response.raw if has_raw else {}
    response_id = None
    if raw:
        response_id = raw.get("id") or raw.get("response_id")
    if response_id:
        return str(response_id), None
    if response.dry_run and response.reason:
        return None, response.reason
    return None, "response_id_missing" if has_raw else "raw_missing"


def classify_order_status_intent(
    ticket_text: str,
    *,
    conversation_id: str,
    event_id: str,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
    client: Optional[OpenAIClient] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> OrderStatusIntentArtifact:
    model = DEFAULT_MODEL
    messages = build_order_status_intent_prompt(ticket_text, metadata=metadata)
    user_length = len(messages[1].content) if len(messages) > 1 else 0
    fingerprint = _prompt_fingerprint(model, len(messages), user_length)
    threshold = get_confidence_threshold()
    gated_reason = _intent_gating_check(
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
    )
    if gated_reason:
        LOGGER.info(
            "order_status_intent.gated",
            extra={
                "event_id": event_id,
                "conversation_id": conversation_id,
                "reason": gated_reason,
                "openai_intent_enabled": get_openai_intent_enabled(),
                "openai_shadow_enabled": get_openai_shadow_enabled(),
                "allow_network": allow_network,
                "outbound_enabled": outbound_enabled,
            },
        )
        return OrderStatusIntentArtifact(
            result=None,
            llm_called=False,
            model=model,
            response_id=None,
            response_id_unavailable_reason=gated_reason,
            confidence_threshold=threshold,
            accepted=False,
            gated_reason=gated_reason,
            prompt_fingerprint=fingerprint,
            ticket_excerpt_redacted=None,
            ticket_excerpt_fingerprint=None,
            dry_run=True,
        )

    excerpt = redact_ticket_text(ticket_text)
    excerpt_fingerprint = _fingerprint(excerpt) if excerpt else None

    request = ChatCompletionRequest(
        model=model,
        messages=messages,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
        metadata={"conversation_id": conversation_id, "event_id": event_id},
        response_format={"type": "json_object"},
    )
    openai_client = client or OpenAIClient(allow_network=allow_network)

    try:
        response = openai_client.chat_completion(
            request, safe_mode=safe_mode, automation_enabled=automation_enabled
        )
    except OpenAIRequestError as exc:
        error_response = exc.response
        response_id, response_id_reason = _response_id_info(error_response)
        LOGGER.warning(
            "order_status_intent.request_failed",
            extra={
                "event_id": event_id,
                "conversation_id": conversation_id,
                "fingerprint": fingerprint,
                "error": str(exc)[:200],
            },
        )
        return OrderStatusIntentArtifact(
            result=None,
            llm_called=True,
            model=error_response.model if error_response else model,
            response_id=response_id,
            response_id_unavailable_reason=response_id_reason or "request_failed",
            confidence_threshold=threshold,
            accepted=False,
            parse_error="request_failed",
            gated_reason=None,
            prompt_fingerprint=fingerprint,
            ticket_excerpt_redacted=excerpt,
            ticket_excerpt_fingerprint=excerpt_fingerprint,
            dry_run=error_response.dry_run if error_response else False,
        )

    response_id, response_id_reason = _response_id_info(response)
    llm_called = not response.dry_run
    result, parse_error = parse_intent_result(
        response.message or "", fallback_text=ticket_text
    )

    if parse_error or not result:
        return OrderStatusIntentArtifact(
            result=None,
            llm_called=llm_called,
            model=response.model,
            response_id=response_id,
            response_id_unavailable_reason=response_id_reason,
            confidence_threshold=threshold,
            accepted=False,
            parse_error=parse_error or "parse_failed",
            gated_reason=None,
            prompt_fingerprint=fingerprint,
            ticket_excerpt_redacted=excerpt,
            ticket_excerpt_fingerprint=excerpt_fingerprint,
            dry_run=response.dry_run,
        )

    accepted = bool(result.is_order_status and result.confidence >= threshold)
    return OrderStatusIntentArtifact(
        result=result,
        llm_called=llm_called,
        model=response.model,
        response_id=response_id,
        response_id_unavailable_reason=response_id_reason,
        confidence_threshold=threshold,
        accepted=accepted,
        parse_error=None,
        gated_reason=None,
        prompt_fingerprint=fingerprint,
        ticket_excerpt_redacted=excerpt,
        ticket_excerpt_fingerprint=excerpt_fingerprint,
        dry_run=response.dry_run,
    )


__all__ = [
    "OrderStatusIntentArtifact",
    "OrderStatusIntentResult",
    "classify_order_status_intent",
    "extract_order_number_from_text",
    "parse_intent_result",
    "redact_ticket_text",
]
