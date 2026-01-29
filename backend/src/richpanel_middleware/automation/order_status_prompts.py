from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

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

REPLY_SYSTEM_PROMPT = """You write a short, friendly order-status reply for a customer.
Use ONLY the provided context; do not invent facts.

Rules:
- If tracking_number or tracking_url is provided, include them verbatim.
- If carrier is provided, include it verbatim.
- If tracking is missing, do NOT include any tracking link or number.
- If tracking is missing and eta_window is provided, mention the ETA window and what to do next.
- If tracking is missing and eta_window is not provided, say a support agent will follow up.
- If shipping_method is provided, mention it in plain language.
- Do NOT invent carriers, tracking numbers, or URLs.
- Avoid internal tags or system jargon (e.g., mw-*, route-*).
- Keep it concise and helpful.

Return strict JSON ONLY with:
{
  "body": "reply text",
  "confidence": 0.0,
  "risk_flags": []
}
"""

_MAX_TICKET_CHARS = 2000
_MAX_DRAFT_CHARS = 2000


@dataclass
class OrderStatusReplyContext:
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    eta_window: Optional[str] = None
    shipping_method: Optional[str] = None
    carrier: Optional[str] = None


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
    safe_context = {
        "tracking_number": context.tracking_number,
        "tracking_url": context.tracking_url,
        "eta_window": context.eta_window,
        "shipping_method": context.shipping_method,
        "carrier": context.carrier,
    }
    context_json = json.dumps(safe_context, sort_keys=True, separators=(",", ":"))
    trimmed_draft = draft_reply[:_MAX_DRAFT_CHARS] if draft_reply else ""
    language_hint = (
        f"Write the reply in language: {language}.\n\n" if language else ""
    )
    user_content = (
        f"{language_hint}"
        "Context (use only these facts):\n"
        f"{context_json}\n\n"
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
