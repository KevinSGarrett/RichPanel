from __future__ import annotations

import html
import re
from typing import List, Optional, Tuple

_HTML_TAG_REGEX = re.compile(r"<[^>]+>")
_EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_REGEX = re.compile(
    r"\b(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)\d{3}[\s\-.]?\d{4}\b"
)
_URL_REGEX = re.compile(r"https?://\S+")
_ADDRESS_REGEX = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.'\- ]{2,40}\s+"
    r"(?:st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|dr|drive|ct|court|"
    r"pl|place|pkwy|parkway|cir|circle|ter|terrace|way)\b\.?",
    flags=re.IGNORECASE,
)
_ORDER_NUMBER_REGEX = re.compile(
    r"(?i)\b(?:order(?:\s*(?:number|no\.?))?\s*[:#]?\s*\d{3,20}|#\d{3,20})\b"
)
_NAME_PATTERNS = [
    re.compile(
        r"(?i)\b(my name is|this is|i am|i'm)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
    ),
    re.compile(
        r"(?im)^(thanks|thank you|cheers|regards|sincerely|best)[, ]+\s*"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
    ),
]


def _mask_order_numbers(text: str) -> Tuple[str, List[str]]:
    tokens: List[str] = []

    def _replace(match: re.Match[str]) -> str:
        tokens.append(match.group(0))
        return f"__ORDER_TOKEN_{len(tokens) - 1}__"

    return _ORDER_NUMBER_REGEX.sub(_replace, text), tokens


def _restore_order_numbers(text: str, tokens: List[str]) -> str:
    restored = text
    for idx, value in enumerate(tokens):
        restored = restored.replace(f"__ORDER_TOKEN_{idx}__", value)
    return restored


def _redact_names(text: str) -> str:
    redacted = text
    for pattern in _NAME_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)} <redacted>", redacted)
    return redacted


def sanitize_for_openai(text: str, *, max_chars: Optional[int] = 2000) -> str:
    if not text:
        return ""
    sanitized = html.unescape(str(text))
    sanitized = _HTML_TAG_REGEX.sub(" ", sanitized)
    sanitized = sanitized.replace("<", " ").replace(">", " ")
    sanitized, order_tokens = _mask_order_numbers(sanitized)
    sanitized = _URL_REGEX.sub("<redacted>", sanitized)
    sanitized = _EMAIL_REGEX.sub("<redacted>", sanitized)
    sanitized = _PHONE_REGEX.sub("<redacted>", sanitized)
    sanitized = _ADDRESS_REGEX.sub("<redacted>", sanitized)
    sanitized = _redact_names(sanitized)
    sanitized = _restore_order_numbers(sanitized, order_tokens)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    if max_chars is not None and len(sanitized) > max_chars:
        sanitized = sanitized[:max_chars].rstrip() + "..."
    return sanitized


__all__ = ["sanitize_for_openai"]
