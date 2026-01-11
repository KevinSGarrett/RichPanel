from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from richpanel_middleware.integrations.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    OpenAIClient,
    OpenAIRequestError,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_REPLY_REWRITE_MODEL") or os.environ.get(
    "OPENAI_MODEL", "gpt-5.2-chat-latest"
)
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENAI_REPLY_REWRITE_MAX_TOKENS", 400))
DEFAULT_CONFIDENCE_THRESHOLD = float(os.environ.get("OPENAI_REPLY_REWRITE_CONFIDENCE_THRESHOLD", 0.7))
DEFAULT_MAX_CHARS = int(os.environ.get("OPENAI_REPLY_REWRITE_MAX_CHARS", 1000))
DEFAULT_ENABLED = False

SUSPICIOUS_PATTERNS = [
    r"password",
    r"ssn",
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"credit card",
    r"\b4\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\b",
    r"\b5\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\b",
    r"social security",
]


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _fingerprint(text: str, *, length: int = 12) -> str:
    try:
        serialized = json.dumps(text, ensure_ascii=False, sort_keys=True)
    except Exception:
        serialized = str(text)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]


def _gating_reason(
    *,
    rewrite_enabled: bool,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
    reply_body: str,
) -> Optional[str]:
    if not rewrite_enabled:
        return "rewrite_disabled"
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
    if not allow_network:
        return "network_disabled"
    if not outbound_enabled:
        return "outbound_disabled"
    if not reply_body:
        return "empty_body"
    return None


def _build_prompt(reply_body: str) -> List[ChatMessage]:
    trimmed = reply_body[: DEFAULT_MAX_CHARS * 2]  # bound input size defensively
    system = (
        "You rewrite Richpanel customer replies. Preserve facts and promises, "
        "avoid new commitments, keep it concise and professional. "
        "Return strict JSON with keys body (string <= 1000 chars), "
        "confidence (0-1 float), risk_flags (list of strings). "
        "If the input seems risky or contains sensitive data, add 'suspicious_content' "
        "to risk_flags and keep the original tone."
    )
    user = f"Rewrite this reply safely:\n\n{trimmed}"
    return [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)]


def _parse_response(
    response: ChatCompletionResponse,
    *,
    fingerprint: str,
) -> Tuple[Optional[str], float, List[str], Optional[str]]:
    """
    Returns (body, confidence, risk_flags, error_reason)
    """
    if response.dry_run or not response.message:
        return None, 0.0, [], response.reason or "dry_run"

    content = response.message.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if fence:
        content = fence.group(1).strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None, 0.0, [], "invalid_json"

    if not isinstance(parsed, dict):
        return None, 0.0, [], "not_a_dict"

    body = parsed.get("body")
    confidence = parsed.get("confidence", 0.0)
    risk_flags = parsed.get("risk_flags") or []
    if body is None or not isinstance(body, str):
        return None, 0.0, [], "missing_body"
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    if not isinstance(risk_flags, list):
        risk_flags = []

    if len(body) > DEFAULT_MAX_CHARS:
        body = body[:DEFAULT_MAX_CHARS]
        risk_flags.append("truncated")

    # Detect obvious risky patterns in the rewritten text.
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, body, flags=re.IGNORECASE):
            risk_flags.append("suspicious_content")
            break

    LOGGER.info(
        "reply_rewrite.parsed",
        extra={
            "fingerprint": fingerprint,
            "confidence": confidence,
            "risk_flags": risk_flags,
            "dry_run": response.dry_run,
            "status": response.status_code,
        },
    )
    return body, confidence, [str(flag) for flag in risk_flags], None


@dataclass
class ReplyRewriteResult:
    body: str
    rewritten: bool
    reason: str
    model: str
    confidence: float
    dry_run: bool
    fingerprint: str
    risk_flags: List[str] = field(default_factory=list)
    gated_reason: Optional[str] = None


def rewrite_reply(
    reply_body: str,
    *,
    conversation_id: str,
    event_id: str,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
    rewrite_enabled: Optional[bool] = None,
    client: Optional[OpenAIClient] = None,
) -> ReplyRewriteResult:
    """
    Attempt to rewrite a deterministic reply via OpenAI.

    Fail-closed: if any gate fails or the model output is low-confidence/unsafe,
    the original reply is returned untouched.
    """
    enabled = rewrite_enabled if rewrite_enabled is not None else _to_bool(
        os.environ.get("OPENAI_REPLY_REWRITE_ENABLED"), default=DEFAULT_ENABLED
    )
    fingerprint = _fingerprint(reply_body or "")
    gating_reason = _gating_reason(
        rewrite_enabled=enabled,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
        reply_body=reply_body or "",
    )
    if gating_reason:
        LOGGER.info(
            "reply_rewrite.gated",
            extra={
                "conversation_id": conversation_id,
                "event_id": event_id,
                "reason": gating_reason,
                "fingerprint": fingerprint,
                "allow_network": allow_network,
                "outbound_enabled": outbound_enabled,
            },
        )
        return ReplyRewriteResult(
            body=reply_body,
            rewritten=False,
            reason=gating_reason,
            model=DEFAULT_MODEL,
            confidence=0.0,
            dry_run=True,
            fingerprint=fingerprint,
            gated_reason=gating_reason,
        )

    messages = _build_prompt(reply_body)
    request = ChatCompletionRequest(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
        metadata={"conversation_id": conversation_id, "event_id": event_id},
    )
    openai_client = client or OpenAIClient(allow_network=allow_network)

    try:
        response = openai_client.chat_completion(
            request, safe_mode=safe_mode, automation_enabled=automation_enabled
        )
    except OpenAIRequestError as exc:
        LOGGER.warning(
            "reply_rewrite.request_failed",
            extra={
                "conversation_id": conversation_id,
                "event_id": event_id,
                "fingerprint": fingerprint,
                "error": str(exc)[:200],
            },
        )
        return ReplyRewriteResult(
            body=reply_body,
            rewritten=False,
            reason="request_failed",
            model=DEFAULT_MODEL,
            confidence=0.0,
            dry_run=False,
            fingerprint=fingerprint,
        )

    rewritten_body, confidence, risk_flags, parse_error = _parse_response(
        response, fingerprint=fingerprint
    )

    if parse_error:
        LOGGER.warning(
            "reply_rewrite.parse_failed",
            extra={
                "conversation_id": conversation_id,
                "event_id": event_id,
                "fingerprint": fingerprint,
                "parse_error": parse_error,
            },
        )
        return ReplyRewriteResult(
            body=reply_body,
            rewritten=False,
            reason=parse_error,
            model=response.model,
            confidence=confidence,
            dry_run=response.dry_run,
            fingerprint=fingerprint,
            risk_flags=risk_flags,
        )

    if confidence < DEFAULT_CONFIDENCE_THRESHOLD or ("suspicious_content" in risk_flags):
        LOGGER.info(
            "reply_rewrite.fallback",
            extra={
                "conversation_id": conversation_id,
                "event_id": event_id,
                "fingerprint": fingerprint,
                "confidence": confidence,
                "risk_flags": risk_flags,
            },
        )
        return ReplyRewriteResult(
            body=reply_body,
            rewritten=False,
            reason="low_confidence" if confidence < DEFAULT_CONFIDENCE_THRESHOLD else "risk_flagged",
            model=response.model,
            confidence=confidence,
            dry_run=response.dry_run,
            fingerprint=fingerprint,
            risk_flags=risk_flags,
        )

    LOGGER.info(
        "reply_rewrite.applied",
        extra={
            "conversation_id": conversation_id,
            "event_id": event_id,
            "fingerprint": fingerprint,
            "confidence": confidence,
            "risk_flags": risk_flags,
            "model": response.model,
        },
    )

    return ReplyRewriteResult(
        body=rewritten_body or reply_body,
        rewritten=True,
        reason="applied",
        model=response.model,
        confidence=confidence,
        dry_run=response.dry_run,
        fingerprint=fingerprint,
        risk_flags=risk_flags,
    )


__all__ = ["rewrite_reply", "ReplyRewriteResult"]

