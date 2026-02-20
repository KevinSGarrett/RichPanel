from __future__ import annotations

import json
from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple

from richpanel_middleware.integrations.openai import ChatMessage

INTENT_SYSTEM_PROMPT = """You are a customer support intent classifier for order status automation.
Decide whether the customer message is asking about order status or tracking.

Return strict JSON ONLY in this exact format:
{
  "is_order_status": true,
  "confidence": 0.0,
  "reason": "short reason",
  "extracted_order_number": "12345" | null,
  "language": "en" | null
}

Rules:
- is_order_status: true only for order status / tracking / shipping status questions.
- confidence: 0.85+ for clear cases, 0.5-0.84 for ambiguous, <0.5 for not order status.
- extracted_order_number: only if explicitly present in the message; otherwise null.
- language: ISO 639-1 code if obvious, else null.
- Do NOT include any personal data, names, emails, or order details in the reason.
- Output JSON only. No extra keys, no commentary, no code fences."""

REPLY_SYSTEM_PROMPT = """You write concise, human-sounding order-status replies in Scentiment's voice.
Use ONLY the provided context and draft facts. Do not invent anything.

NON-NEGOTIABLES
- Output strict JSON ONLY: {"body":"...","confidence":0.xx,"risk_flags":[]}. No commentary, no code fences.
- Never mention AI, bots, automation, templates, or system prompts.
- Do not add new commitments (refunds, discounts, guarantees, policy exceptions).
- Do not invent dates, carriers, tracking numbers, or URLs.
- Preserve any URLs, tracking numbers, ETA windows, and delivery date ranges already present in the draft verbatim.
- Do NOT include a greeting or signature in the body (pipeline adds those).
- Do NOT encourage inbound contact (no "reply", "reply back", "reply here", "reach out", "contact us", "let us know", "message us", "get back to us", "email us", "call us", "contact support", "our support team", "if you have questions", "we're here to help").
- Do NOT output a "Key Details" title or any checklist/bulleted block.

VOICE
- Kind, calm, confident, professional. Concise but fully informative.
- No slang, no emojis, no exclamation-heavy tone.
- Avoid internal/system phrasing (mw-*, route-*, "marked as", "scheduled to").

CUSTOMER ANCHORING (REQUIRED)
- If customer_message_excerpt is present, the first 1-2 sentences MUST:
  (1) paraphrase the customer's concern, and
  (2) include ONE concrete anchor detail from the excerpt (no verbatim quoting).
  Examples of anchor details: "it's been a week", "no tracking", "hasn't arrived", "label created", "need it by Friday".

TONE (REQUIRED)
Infer tone from customer_message_excerpt:
- Angry/frustrated: MUST include exactly ONE apology sentence ("I'm sorry ..." or "I apologize ..."), then be direct.
- Anxious/urgent: calm reassurance, then clear timeline.
- Confused: simplify and restate the key facts clearly.
- Neutral: friendly and direct.
Do not over-apologize.

FORMATTING (CRITICAL)
- Use 2-3 short paragraphs with a blank line between them.
- Max 2 sentences per paragraph.
- Avoid long comma-chains. Prefer periods.
- Do NOT cram all timing facts into one sentence.

CONTENT RULES
- If tracking_number or tracking_url is provided: include them verbatim.
- If carrier is provided: include it verbatim.
- If tracking is missing: do not include any tracking link or number.
- If tracking is missing and timing facts exist in the draft: include processing time + shipping time + total ETA window + delivery date range, using short sentences.
- If shipping_method is provided: mention it in plain language, WITHOUT embedding the shipping window inside the method name (no "Standard (3-7 business days)").

CANNED PHRASES TO AVOID (DO NOT USE)
- "Thanks for your patience."
- "Your order is marked as..."
- "It is scheduled to..."
- "With Standard (X-Y business days) shipping..."

OUTPUT FORMAT (STRICT JSON)
Return ONLY valid JSON:
{
  "body": "reply text",
  "confidence": 0.0,
  "risk_flags": []
}

risk_flags examples:
- "customer_frustrated"
- "customer_deadline"
- "missing_tracking_info"
- "preorder_explanation_needed"
"""

_MAX_TICKET_CHARS = 2000
_MAX_DRAFT_CHARS = 2000

_MONTH_NAME_PATTERN = (
    r"January|February|March|April|May|June|July|August|September|October|November|December"
)
_ETA_RANGE_REGEX = re.compile(
    r"\b(\d+)\s*(?:-|–|to)\s*(\d+)\s*(business\s+days?|bd|days?)\b",
    flags=re.IGNORECASE,
)
_ETA_SINGLE_REGEX = re.compile(
    r"\b(\d+)\s*(business\s+days?|bd|days?)\b", flags=re.IGNORECASE
)
_DATE_RANGE_SAME_YEAR_REGEX = re.compile(
    rf"\b(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}}\s*(?:–|-|to)\s*"
    rf"(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}},\s*\d{{4}}\b",
    flags=re.IGNORECASE,
)
_DATE_RANGE_DIFFERENT_YEAR_REGEX = re.compile(
    rf"\b(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}},\s*\d{{4}}\s*(?:–|-|to)\s*"
    rf"(?:{_MONTH_NAME_PATTERN})\s+\d{{1,2}},\s*\d{{4}}\b",
    flags=re.IGNORECASE,
)


def _normalize_eta_unit(unit: str) -> str:
    return re.sub(r"\s+", " ", unit.strip().lower())


def _normalize_date_window(token: str) -> str:
    normalized = token.strip().lower()
    normalized = re.sub(r"\s*(?:–|-)\s*", "-", normalized)
    normalized = re.sub(r"\s*\bto\b\s*", "-", normalized)
    normalized = re.sub(r"\s*,\s*", ", ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


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
    return list(dict.fromkeys(windows))


def _extract_date_windows(text: str) -> List[str]:
    if not text:
        return []
    windows: List[str] = []
    for match in _DATE_RANGE_SAME_YEAR_REGEX.finditer(text):
        windows.append(_normalize_date_window(match.group(0)))
    for match in _DATE_RANGE_DIFFERENT_YEAR_REGEX.finditer(text):
        windows.append(_normalize_date_window(match.group(0)))
    return list(dict.fromkeys(windows))


def _build_required_verbatim_tokens(draft_reply: str) -> List[str]:
    if not draft_reply:
        return []
    required = _extract_eta_windows(draft_reply) + _extract_date_windows(draft_reply)
    return list(dict.fromkeys(required))


@dataclass
class OrderStatusReplyContext:
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    eta_window: Optional[str] = None
    shipping_method: Optional[str] = None
    carrier: Optional[str] = None
    customer_first_name: Optional[str] = None
    customer_message_excerpt: Optional[str] = None

    def as_payload(self) -> Dict[str, Optional[str]]:
        payload = {
            "tracking_number": self.tracking_number,
            "tracking_url": self.tracking_url,
            "eta_window": self.eta_window,
            "shipping_method": self.shipping_method,
            "carrier": self.carrier,
            "customer_first_name": self.customer_first_name,
            "customer_message_excerpt": self.customer_message_excerpt,
        }
        return {key: value for key, value in payload.items() if value is not None}


def build_order_status_intent_prompt(
    ticket_text: str, *, metadata: Optional[Dict[str, str]] = None
) -> List[ChatMessage]:
    trimmed = ticket_text[:_MAX_TICKET_CHARS] if ticket_text else ""
    meta = metadata or {}
    meta_json = json.dumps(meta, sort_keys=True, separators=(",", ":"))
    user_content = (
        "Ticket message:\n"
        f"{trimmed}\n\n"
        "Metadata (non-PII):\n"
        f"{meta_json}"
    )
    return [
        ChatMessage(role="system", content=INTENT_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]


def build_order_status_reply_prompt(
    *,
    context: OrderStatusReplyContext,
    draft_reply: str,
    language: Optional[str] = None,
) -> List[ChatMessage]:
    safe_context = context.as_payload()
    context_json = json.dumps(safe_context, sort_keys=True, separators=(",", ":"))
    trimmed_draft = draft_reply[:_MAX_DRAFT_CHARS] if draft_reply else ""
    language_hint = (
        f"Write the reply in language: {language}.\n\n" if language else ""
    )
    required_tokens = _build_required_verbatim_tokens(trimmed_draft)
    required_block = ""
    if required_tokens:
        required_lines = "\n".join(f"- {token}" for token in required_tokens)
        required_block = (
            "Required Verbatim Tokens (MUST appear exactly as written):\n"
            f"{required_lines}\n\n"
        )
    user_content = (
        f"{language_hint}"
        "Context (use only these facts):\n"
        f"{context_json}\n\n"
        f"{required_block}"
        "Draft reply (facts to preserve):\n"
        f"{trimmed_draft}"
    )
    return [
        ChatMessage(role="system", content=REPLY_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]


__all__ = [
    "OrderStatusReplyContext",
    "build_order_status_intent_prompt",
    "build_order_status_reply_prompt",
]
