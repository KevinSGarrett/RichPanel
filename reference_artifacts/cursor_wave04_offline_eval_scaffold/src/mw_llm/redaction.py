"""PII redaction helpers for evaluation + logs."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
     r"(?:\+?\d[\s\-\(\)]*)?(?:\d[\s\-\(\)]*){9,}\d", re.IGNORECASE
)
ORDER_PATTERN = re.compile(
     r"\b(order(?:\s*(?:number|no|#))?[:\-\s]*[A-Z0-9\-]{4,})\b", re.IGNORECASE
)
TRACKING_PATTERN = re.compile(
     r"\b(1Z[0-9A-Z]{16}|9[2345]\d{20,22}|[A-Z]{2}\d{9}US|\d{12,})\b", re.IGNORECASE
)


REDACTION_TOKENS = {
     "email": "[REDACTED_EMAIL]",
     "phone": "[REDACTED_PHONE]",
     "order": "[REDACTED_ORDER]",
     "tracking": "[REDACTED_TRACKING]",
}


@dataclass(slots=True)
class RedactionResult:
     redacted_text: str
     matches: Dict[str, List[str]]


def _apply(pattern: re.Pattern[str], token_key: str, text: str, matches: Dict[str, List[str]]) -> str:
     replacement = REDACTION_TOKENS[token_key]

     def _sub(match: re.Match[str]) -> str:
         matches.setdefault(token_key, []).append(match.group(0))
         return replacement

     return pattern.sub(_sub, text)


def redact_text(text: str | None) -> RedactionResult:
     if not text:
         return RedactionResult(redacted_text="", matches={})

     matches: Dict[str, List[str]] = {}
     redacted = text
     redacted = _apply(EMAIL_PATTERN, "email", redacted, matches)
     redacted = _apply(PHONE_PATTERN, "phone", redacted, matches)
     redacted = _apply(ORDER_PATTERN, "order", redacted, matches)
     redacted = _apply(TRACKING_PATTERN, "tracking", redacted, matches)
     return RedactionResult(redacted_text=redacted, matches=matches)


def contains_order_number(text: str | None) -> bool:
     return bool(text and ORDER_PATTERN.search(text))


def contains_tracking_number(text: str | None) -> bool:
     return bool(text and TRACKING_PATTERN.search(text))


def contains_phone(text: str | None) -> bool:
     return bool(text and PHONE_PATTERN.search(text))


def contains_email(text: str | None) -> bool:
     return bool(text and EMAIL_PATTERN.search(text))
