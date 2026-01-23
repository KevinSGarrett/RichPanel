from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from urllib.parse import parse_qs, urlparse
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from richpanel_middleware.integrations.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    OpenAIClient,
    OpenAIRequestError,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_REPLY_REWRITE_MODEL", "") or os.environ.get(
    "OPENAI_MODEL", "gpt-5.2-chat-latest"
)
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENAI_REPLY_REWRITE_MAX_TOKENS", 400))
DEFAULT_CONFIDENCE_THRESHOLD = float(
    os.environ.get("OPENAI_REPLY_REWRITE_CONFIDENCE_THRESHOLD", 0.7)
)
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

_URL_REGEX = re.compile(r"https?://[^\s<>()\"']+")
_ETA_RANGE_REGEX = re.compile(
    r"\b(\d+)\s*(?:-|–|to)\s*(\d+)\s*(business\s+days?|bd|days?)\b",
    flags=re.IGNORECASE,
)
_ETA_SINGLE_REGEX = re.compile(
    r"\b(\d+)\s*(business\s+days?|bd|days?)\b", flags=re.IGNORECASE
)


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
        "Do not add new promises. Do not remove compliance or safety language. "
        "If the input includes any URLs, they must appear verbatim in the output. "
        "If the input includes tracking numbers, they must appear verbatim in the output. "
        "If the input includes an ETA window (for example, '1-3 business days'), "
        "preserve the numbers and units exactly. "
        "Return strict JSON ONLY (no commentary, no code fences) with keys "
        "body (string <= 1000 chars), confidence (0-1 float), "
        "risk_flags (list of strings). "
        "If the input seems risky or contains sensitive data, add 'suspicious_content' "
        "to risk_flags and keep the original tone."
    )
    user = f"Rewrite this reply safely:\n\n{trimmed}"
    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=user),
    ]


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _strip_url_punctuation(url: str) -> str:
    trimmed = url.strip()
    while trimmed and trimmed[-1] in ".,;:!?)]}'\"":
        trimmed = trimmed[:-1]
    return trimmed


def _extract_urls(text: str) -> List[str]:
    if not text:
        return []
    matches = _URL_REGEX.findall(text)
    normalized = [_strip_url_punctuation(match) for match in matches]
    return _dedupe([url for url in normalized if url])


def _is_tracking_token(token: str) -> bool:
    if not token or len(token) < 6:
        return False
    if not any(char.isdigit() for char in token):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9-]+", token))


def _extract_tracking_from_url(url: str) -> List[str]:
    tokens: List[str] = []
    try:
        parsed = urlparse(url)
    except Exception:
        return tokens
    query = parse_qs(parsed.query)
    for key in (
        "tracknum",
        "tracking",
        "tracking_number",
        "trackingnumber",
        "trackingno",
        "tracking_code",
        "trackingcode",
        "trackingid",
    ):
        for value in query.get(key, []):
            candidate = value.strip()
            if _is_tracking_token(candidate):
                tokens.append(candidate)
    if parsed.path:
        segments = [segment for segment in parsed.path.split("/") if segment]
        if segments:
            candidate = segments[-1].strip()
            if _is_tracking_token(candidate):
                tokens.append(candidate)
    return tokens


def _extract_tracking_tokens(text: str) -> List[str]:
    if not text:
        return []
    tokens: List[str] = []
    label_pattern = re.compile(
        r"(?i)\btracking(?:\s*(?:number|no\.?|#))?\s*[:\-]?\s*([A-Za-z0-9-]{6,})"
    )
    for token in label_pattern.findall(text):
        candidate = token.strip()
        if _is_tracking_token(candidate):
            tokens.append(candidate)
    for url in _extract_urls(text):
        tokens.extend(_extract_tracking_from_url(url))
    return _dedupe(tokens)


def _normalize_eta_unit(unit: str) -> str:
    return re.sub(r"\s+", " ", unit.strip().lower())


def _extract_eta_windows(text: str) -> List[str]:
    if not text:
        return []
    windows: List[str] = []
    spans: List[Tuple[int, int]] = []
    for match in _ETA_RANGE_REGEX.finditer(text):
        spans.append(match.span())
        min_days = match.group(1)
        max_days = match.group(2)
        unit = _normalize_eta_unit(match.group(3))
        windows.append(f"{min_days}-{max_days} {unit}")
    for match in _ETA_SINGLE_REGEX.finditer(text):
        start, end = match.span()
        if any(start < span_end and end > span_start for span_start, span_end in spans):
            continue
        days = match.group(1)
        unit = _normalize_eta_unit(match.group(2))
        windows.append(f"{days} {unit}")
    return _dedupe(windows)


def _missing_required_tokens(
    original: str, rewritten: str
) -> Tuple[List[str], List[str], List[str]]:
    required_urls = _extract_urls(original)
    rewritten_urls = _extract_urls(rewritten)
    required_tracking = _extract_tracking_tokens(original)
    rewritten_tracking = _extract_tracking_tokens(rewritten)
    required_eta = _extract_eta_windows(original)
    rewritten_eta = _extract_eta_windows(rewritten)
    missing_urls = [url for url in required_urls if url not in rewritten_urls]
    missing_tracking = [
        token for token in required_tracking if token not in rewritten_tracking
    ]
    missing_eta = [window for window in required_eta if window not in rewritten_eta]
    return missing_urls, missing_tracking, missing_eta


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
        extracted = _extract_json_object(content)
        if not extracted:
            return None, 0.0, [], "invalid_json"
        try:
            parsed = json.loads(extracted)
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
    llm_called: bool = False
    response_id: Optional[str] = None
    response_id_unavailable_reason: Optional[str] = None
    error_class: Optional[str] = None
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
    enabled = (
        rewrite_enabled
        if rewrite_enabled is not None
        else _to_bool(
            os.environ.get("OPENAI_REPLY_REWRITE_ENABLED"), default=DEFAULT_ENABLED
        )
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
            llm_called=False,
            response_id=None,
            response_id_unavailable_reason=gating_reason,
            error_class=None,
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

    response: Optional[ChatCompletionResponse]
    try:
        response = openai_client.chat_completion(
            request, safe_mode=safe_mode, automation_enabled=automation_enabled
        )
    except OpenAIRequestError as exc:
        error_response: Optional[ChatCompletionResponse] = exc.response
        response_id, response_id_reason = _response_id_info(error_response)
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
            model=error_response.model if error_response else DEFAULT_MODEL,
            confidence=0.0,
            dry_run=error_response.dry_run if error_response else False,
            fingerprint=fingerprint,
            llm_called=True,
            response_id=response_id,
            response_id_unavailable_reason=response_id_reason or "request_failed",
            error_class=exc.__class__.__name__,
        )

    if response is None:
        return ReplyRewriteResult(
            body=reply_body,
            rewritten=False,
            reason="no_response",
            model=DEFAULT_MODEL,
            confidence=0.0,
            dry_run=True,
            fingerprint=fingerprint,
            llm_called=False,
            response_id=None,
            response_id_unavailable_reason="no_response",
            error_class=None,
        )

    response_id, response_id_reason = _response_id_info(response)
    llm_called = not response.dry_run
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
            llm_called=llm_called,
            response_id=response_id,
            response_id_unavailable_reason=response_id_reason,
            risk_flags=risk_flags,
        )

    missing_urls, missing_tracking, missing_eta = _missing_required_tokens(
        reply_body, rewritten_body
    )
    if missing_urls or missing_tracking or missing_eta:
        reason = "missing_required_tokens"
        if missing_urls and not missing_tracking and not missing_eta:
            reason = "missing_required_urls"
        elif missing_tracking and not missing_urls and not missing_eta:
            reason = "missing_required_tracking"
        elif missing_eta and not missing_urls and not missing_tracking:
            reason = "missing_required_eta"
        LOGGER.info(
            "reply_rewrite.validation_failed",
            extra={
                "conversation_id": conversation_id,
                "event_id": event_id,
                "fingerprint": fingerprint,
                "missing_urls": len(missing_urls),
                "missing_tracking": len(missing_tracking),
                "missing_eta": len(missing_eta),
            },
        )
        return ReplyRewriteResult(
            body=reply_body,
            rewritten=False,
            reason=reason,
            model=response.model,
            confidence=confidence,
            dry_run=response.dry_run,
            fingerprint=fingerprint,
            llm_called=llm_called,
            response_id=response_id,
            response_id_unavailable_reason=response_id_reason,
            risk_flags=risk_flags,
        )

    if confidence < DEFAULT_CONFIDENCE_THRESHOLD or (
        "suspicious_content" in risk_flags
    ):
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
            reason=(
                "low_confidence"
                if confidence < DEFAULT_CONFIDENCE_THRESHOLD
                else "risk_flagged"
            ),
            model=response.model,
            confidence=confidence,
            dry_run=response.dry_run,
            fingerprint=fingerprint,
            llm_called=llm_called,
            response_id=response_id,
            response_id_unavailable_reason=response_id_reason,
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
        llm_called=llm_called,
        response_id=response_id,
        response_id_unavailable_reason=response_id_reason,
        risk_flags=risk_flags,
    )


__all__ = ["rewrite_reply", "ReplyRewriteResult"]
