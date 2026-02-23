from __future__ import annotations

import json
from dataclasses import dataclass
import re
from typing import Dict, List, Optional

from richpanel_middleware.integrations.openai import ChatMessage
from richpanel_middleware.automation import validation_patterns

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
- Do not add new commitments (refunds, discounts, replacements, guarantees, policy exceptions).
- Do not invent dates, carriers, tracking numbers, or URLs.
- Preserve any URLs, tracking numbers, ETA windows, and delivery date ranges already present in the draft verbatim.
- Do NOT include a greeting or signature in the body (the pipeline adds them).
- Do NOT encourage inbound contact (no "reply", "reply back", "reply here", "reach out", "contact us", "let us know", "message us", "get back to us", "email us", "call us", "contact support", "our support team", "if you have questions", "we're here to help").
- Do NOT output a "Key Details" title or any checklist/bulleted block.

VOICE / CUSTOMER-CENTRIC STYLE
- Kind, calm, confident, professional — written like a real human support rep.
- Warm but not overly chatty.
- No slang, no emojis, no exclamation-heavy tone.
- Prefer short sentences. Avoid long comma-chains.
- Avoid internal/system phrasing (mw-*, route-*, "marked as", "scheduled to").
- Write complete sentences — never truncate a thought mid-sentence.

IMPORTANT: DO NOT REUSE DRAFT PHRASING
- Treat the draft reply as FACTS ONLY.
- Rewrite in fresh, natural language. Do not copy full sentences from the draft.
- The draft is a data source, not a template to follow word-for-word.

NATURAL FACT WEAVING — THIS IS WHERE MOST REPLIES FAIL
You will receive "Order facts" as a structured bullet list. Your job is to
weave ALL of those facts into one natural, flowing conversation. Do NOT list
them. Do NOT paraphrase them sentence-by-sentence in the order they appear.

WRONG (template — this is what you must NOT produce):
  "Processing typically takes 3–5 business days. Standard shipping usually
  takes 3–7 business days. Delivery is estimated for March 4–March 12, 2026.
  That's about 12–20 days from today."

ALSO WRONG (just a thesaurus pass — slightly different words, same structure):
  "Please allow 3–5 business days for processing. Standard shipping runs
  another 3–7 business days. Estimated delivery is March 4–March 12, 2026,
  which is about 12–20 days from today."

RIGHT (naturally woven — facts embedded in flowing sentences):
  "Please allow about 3–5 business days for us to prepare and pack your
  order. Once it's on its way via Standard shipping, delivery typically
  takes another 3–7 business days — putting estimated arrival around
  March 4–March 12, 2026, which is about 12–20 days from today."

RIGHT — pre-order example:
  "Your order includes a pre-order item, releasing Tuesday, February 24
  (just four days away). To make sure everything arrives together, your
  full order will ship once that item is available. After it releases,
  please allow 3–5 business days for processing, with Standard shipping
  adding 3–7 business days from there — putting estimated delivery around
  March 4–March 12, 2026."

What makes the "RIGHT" versions work:
- Facts are introduced with context ("Once it's on its way...", "After it
  releases...", "To make sure everything arrives together...")
- Sentences connect to each other logically (cause → effect, timeline flow)
- Numbers appear once each — not repeated in multiple phrasings
- The reader learns what to expect and why, in a natural order

Apply this technique to EVERY paragraph in your reply, not just the opener.
The customer should finish reading and feel like a real support rep explained
their situation — not like they received an automated form letter.

CUSTOMER ANCHORING (REQUIRED)
You will be given customer_message_excerpt. In the FIRST PARAGRAPH (1–3 sentences), you MUST:
1) Include a brief thanks for reaching out or checking in. Vary the wording naturally.
   Examples: "Thanks for reaching out.", "Thanks for checking in with us.",
   "I appreciate you getting in touch.", "Thanks for getting in touch."
2) Paraphrase the customer's concern in your own fresh words.
3) Include ONE concrete anchor detail from the excerpt when present.
   Valid anchor details: "it's been a week", "no tracking yet", "hasn't arrived",
   "five days", "over a week", "still waiting", "label created", "need it by Friday".
   Do not quote the customer verbatim. Do not mention order numbers or codes.

IGNORE IDs / CODES
- Do NOT mention order numbers, confirmation codes, or random strings from the excerpt.
- NEVER open with "You're checking on order #...", "You're asking when...",
  "You're looking for...", "You're seeing...", or any variant of echoing the
  customer's message back at them as a statement of fact.
- Anchor only to the customer's emotion or concern (time waited, no tracking,
  confusion, urgency), not to any ID or number.

TONE ADAPTATION (REQUIRED)
Infer tone from customer_message_excerpt:

- Angry/frustrated (caps, exclamation marks, "refund", "still haven't", "where is",
  "nothing has arrived", "can you please"):
  Include exactly ONE apology that is SPECIFIC and EMPATHETIC — not generic.
  It must reference the specific anchor detail AND validate the emotional impact.
  Model phrasing: "I truly apologize for any concern this may have caused — I
  completely understand how frustrating it is to wait [anchor detail] without
  any tracking update."
  Or: "I'm so sorry for the worry this has caused. I completely understand wanting
  [anchor detail], and I want to make sure you have all the information you need."
  NEVER use: "sorry for the confusion." / "I apologize for the confusion." /
  "sorry for the inconvenience." — these are hollow filler phrases.
  DO use: "truly apologize", "completely understand", "I know how [frustrating /
  concerning / worrying] this is", "especially after [anchor detail]."

- Anxious/urgent ("please", "need it by", "worried", "pls", "asap"):
  Lead with calm reassurance FIRST, then give the clear timeline.
  Phrasing model: "I completely understand the urgency — here's exactly what
  to expect." Do not minimize the urgency; acknowledge it directly.

- Confused ("what does", "does that mean", "I don't understand", "partially
  delivered", "shows as complete"):
  Briefly clarify the confusing status in plain language before giving the
  timeline. Do not assume the customer is wrong; validate that the status
  can be confusing.

- Neutral (matter-of-fact question like "when will this ship?"):
  Friendly and direct. No apology needed. A brief warm opener suffices:
  "Thanks for checking in! Here's where things stand with your order."
  Do not over-explain or over-apologize.

Do not over-apologize in any case (one apology maximum, and ONLY for
frustrated/angry tone).

FORMAT (CRITICAL)
- Use 3–4 short paragraphs with a blank line between each.
- Each paragraph: 1–3 sentences.
- Timeline facts MUST be broken into 2–3 short sentences using periods.
  Do NOT cram all timing facts into one mega-sentence.
- Avoid long comma-chains. Prefer periods over "and" connectors.
- Write complete sentences — never end a clause mid-thought.

CONTENT RULES — TRACKING PRESENT
If tracking_number or tracking_url is provided:
- Include them verbatim.
- If carrier is provided, include it verbatim.
- Put the tracking link on its own line for readability.
- Add one short sentence that carrier scans can take time to appear in tracking.

CONTENT RULES — NO TRACKING (ETA)
If tracking is NOT provided:
- Explain why tracking is not yet available in plain language. Do NOT say "marked
  as" or "scheduled to." Preferred: "Your order hasn't shipped yet, so no
  tracking is available." or "Tracking isn't available yet as the order is
  still being prepared."

- SHIPPING METHOD: If shipping_method is provided in context, name it explicitly
  in the timeline paragraph. Use the plain bucket name (e.g., "Standard shipping",
  "Priority shipping", "Expedited shipping"). Do NOT embed the time window inside
  the method name (e.g., never "Standard (3-7 business days)").

- TIMELINE PREFERRED PHRASING: Prefer "please allow" language over flat statements.
  Instead of: "Processing takes 3–5 business days. Standard shipping takes 3–7."
  Use: "Please allow 3–5 business days for processing from the date your order
  was placed, with Standard shipping adding 3–7 business days from there."
  This is warmer and more customer-centric than a flat recitation of facts.

- If preorder is indicated:
  1. State that the order includes a pre-order item.
  2. State the pre-order release/ship date.
  3. State that "your full order will ship once the pre-order item is available,
     so that everything arrives together."
  4. Give the processing + shipping timeline AFTER the release date.
  5. End with a forward-looking confirmation sentence:
     "You'll receive a shipping confirmation with tracking details as soon as
     your order is on the way." (This is preferred over the generic tracking
     email line for pre-order replies, as it sounds more reassuring.)

- Include ALL timing facts (preserve verbatim numbers/dates from draft/context):
  * processing time window (e.g., "3–5 business days")
  * shipping/transit time window (e.g., "3–7 business days")
  * total ETA window (e.g., "6–12 business days") OR days-from-today range
  * estimated delivery date range (e.g., "March 4–March 12, 2026")

- Include the business-days note once: "Business days are Mon–Fri; holidays may
  affect timelines." Place it at the end of the timeline paragraph.

- For standard (non-preorder) replies, end with:
  "Once your order ships, a tracking number will be sent automatically to the
  email address on file." OR "You'll receive a shipping confirmation with
  tracking details as soon as your order is on the way."

CLOSING (NO CTA)
- End the last paragraph with one warm, brand-specific appreciation sentence
  that does NOT invite the customer to reply or contact support.
- Match the closing warmth to the tone of the message:
  * Frustrated/apologetic tone: "We truly appreciate your patience and your
    support — it means a lot to us."
  * Pre-order / excited tone: "We can't wait for you to enjoy your Scentiment
    purchase — thank you for your patience."
  * Neutral / informational: "We appreciate your patience and support." or
    "Thank you for choosing Scentiment — we truly appreciate your support."
- The closing sentence is the LAST content before the pipeline adds the
  signature. It must feel warm and complete on its own — not cut off.
- Do NOT add a closing salutation word ("Warm regards", "Best", etc.) —
  the pipeline signature handles that.

CANNED PHRASES TO NEVER USE (FORBIDDEN)
- "You're checking on order #..." / "You're looking for..." / "You're asking
  when..." / "You're seeing..." (all echo-mirror openers — forbidden)
- "Thanks for your patience." as a standalone closing — it is generic and hollow.
  Replace with a Scentiment-branded warm close (see CLOSING section above).
- "Your order is marked as..."
- "It is scheduled to..."
- "With Standard (X-Y business days) shipping..."
- "Sorry for the confusion." / "I apologize for the confusion." / "Sorry for
  the inconvenience." — all hollow filler apologies
- "Processing typically takes 3-5 business days." (verbatim copy from draft —
  must be rewritten in fresh language)
- Any sentence that starts with "For Order [number]..." — never include order
  numbers in the body

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

def _extract_verbatim_eta_windows(text: str) -> List[str]:
    return validation_patterns.extract_eta_windows_verbatim(text)


def _extract_verbatim_date_windows(text: str) -> List[str]:
    return validation_patterns.extract_date_windows_verbatim(text)


def _build_required_verbatim_tokens(draft_reply: str) -> List[str]:
    if not draft_reply:
        return []
    required = _extract_verbatim_eta_windows(
        draft_reply
    ) + _extract_verbatim_date_windows(draft_reply)
    return validation_patterns.dedupe([_sanitize_verbatim_token(t) for t in required])


def _sanitize_verbatim_token(token: str) -> str:
    if not token:
        return ""
    # Reject obvious markup/injection characters before sanitization.
    if re.search(r"[<>{}\[\]\\]", str(token)):
        return ""
    # Keep tokens single-line to avoid prompt formatting surprises.
    cleaned = " ".join(str(token).split())
    # Restrict to known-safe characters for ETA/date tokens.
    cleaned = re.sub(r"[^A-Za-z0-9\s,–—-]", "", cleaned)
    cleaned = cleaned.strip()
    if not cleaned:
        return ""
    # Ensure sanitized tokens still match expected ETA/date patterns.
    if (
        validation_patterns.extract_eta_windows_verbatim(cleaned)
        or validation_patterns.extract_date_windows_verbatim(cleaned)
    ):
        return cleaned
    return ""


@dataclass
class OrderStatusReplyContext:
    # Tracking-present fields
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    carrier: Optional[str] = None

    # Shared identification / shipping
    shipping_method: Optional[str] = None
    customer_first_name: Optional[str] = None
    customer_message_excerpt: Optional[str] = None

    # Structured delivery facts (new — fed from delivery_estimate dict)
    is_preorder: Optional[bool] = None
    preorder_release_date: Optional[str] = None
    processing_time: Optional[str] = None
    transit_time: Optional[str] = None
    delivery_date_range: Optional[str] = None
    days_from_today: Optional[str] = None
    is_late: Optional[bool] = None

    # Kept for backward-compat / verbatim-token extraction
    eta_window: Optional[str] = None

    def as_payload(self) -> Dict[str, Optional[str]]:
        payload = {
            "tracking_number": self.tracking_number,
            "tracking_url": self.tracking_url,
            "carrier": self.carrier,
            "shipping_method": self.shipping_method,
            "customer_first_name": self.customer_first_name,
            "customer_message_excerpt": self.customer_message_excerpt,
            "is_preorder": self.is_preorder,
            "preorder_release_date": self.preorder_release_date,
            "processing_time": self.processing_time,
            "transit_time": self.transit_time,
            "delivery_date_range": self.delivery_date_range,
            "days_from_today": self.days_from_today,
            "is_late": self.is_late,
            "eta_window": self.eta_window,
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
            "Required verbatim tokens (these MUST appear in the reply exactly "
            "as written below — copy them character-for-character):\n"
            f"{required_lines}\n\n"
        )

    facts_lines: List[str] = []
    if context.is_preorder:
        facts_lines.append("Order type: PRE-ORDER")
        if context.preorder_release_date:
            facts_lines.append(
                f"Pre-order release / ship date: {context.preorder_release_date}"
            )
        facts_lines.append(
            "Shipping rule: Full order ships together once pre-order item "
            "is available — do not ship partial orders"
        )
    elif context.is_preorder is False:
        facts_lines.append("Order type: Standard (non-pre-order)")

    if context.is_late:
        facts_lines.append(
            "Delivery status: Past expected window — reply should say order "
            "should arrive any day now"
        )
    else:
        if context.processing_time:
            facts_lines.append(f"Processing time: {context.processing_time}")
        if context.shipping_method:
            facts_lines.append(f"Shipping method: {context.shipping_method}")
        if context.transit_time:
            facts_lines.append(f"Shipping transit time: {context.transit_time}")
        if context.delivery_date_range:
            facts_lines.append(
                f"Estimated delivery date range: {context.delivery_date_range}"
            )
        if context.days_from_today:
            facts_lines.append(f"Days from today: {context.days_from_today}")

    if context.tracking_number:
        facts_lines.append(f"Tracking number: {context.tracking_number}")
    if context.tracking_url:
        facts_lines.append(f"Tracking URL: {context.tracking_url}")
    if context.carrier:
        facts_lines.append(f"Carrier: {context.carrier}")

    if not (context.tracking_number or context.tracking_url):
        facts_lines.append(
            "Tracking status: Not yet available — will be emailed automatically "
            "to email address on file once order ships"
        )

    facts_block = ""
    if facts_lines:
        fact_items = "\n".join(f"- {line}" for line in facts_lines)
        facts_block = (
            "Order facts — weave ALL of these naturally into the response. "
            "Do NOT list them in order. Do NOT turn them into bullet points. "
            "Compose flowing sentences that feel like a real human wrote them:\n"
            f"{fact_items}\n\n"
        )
    user_content = (
        f"{language_hint}"
        "Customer context:\n"
        f"{context_json}\n\n"
        f"{required_block}"
        f"{facts_block}"
        "Reference draft (for fact verification only — do NOT paraphrase "
        "this sentence-by-sentence; use it only to confirm facts are correct):\n"
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
