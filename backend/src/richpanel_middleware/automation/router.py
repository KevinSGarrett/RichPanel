from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from richpanel_middleware.commerce.order_lookup import _extract_order_number_from_payload

DEPARTMENTS = {
    "Sales Team",
    "Backend Team",
    "Technical Support Team",
    "Phone Support Team",
    "TikTok Support",
    "Returns Admin",
    "LiveChat Support",
    "Leadership Team",
    "Social Media Team",
    "Email Support Team",
    "Chargebacks / Disputes Team",
}

INTENT_TO_DEPARTMENT = {
    "order_status_tracking": "Email Support Team",
    "shipping_delay_not_shipped": "Email Support Team",
    "delivered_not_received": "Returns Admin",
    "missing_items_in_shipment": "Returns Admin",
    "wrong_item_received": "Returns Admin",
    "damaged_item": "Returns Admin",
    "cancel_order": "Email Support Team",
    "address_change_order_edit": "Email Support Team",
    "cancel_subscription": "Email Support Team",
    "billing_issue": "Email Support Team",
    "promo_discount_issue": "Sales Team",
    "pre_purchase_question": "Sales Team",
    "influencer_marketing_inquiry": "Social Media Team",
    "return_request": "Returns Admin",
    "exchange_request": "Returns Admin",
    "refund_request": "Returns Admin",
    "technical_support": "Technical Support Team",
    "phone_support_request": "Phone Support Team",
    "tiktok_support_request": "TikTok Support",
    "social_media_support_request": "Social Media Team",
    "chargeback_dispute": "Chargebacks / Disputes Team",
    "legal_threat": "Leadership Team",
    "harassment_threats": "Leadership Team",
    "fraud_suspected": "Leadership Team",
    "unknown_other": "Email Support Team",
    "unknown": "Email Support Team",
}

DEFAULT_DEPARTMENT = "Email Support Team"
DEFAULT_TAG = "mw-routing-applied"

ORDER_STATUS_KEYWORDS = (
    "where is my order",
    "order status",
    "tracking",
    "track",
    "shipment",
    "shipping",
    "delivered",
    "delivery",
    "arrive",
    "package",
    "fulfillment",
)
ORDER_STATUS_CANDIDATE_KEYWORDS = ORDER_STATUS_KEYWORDS + (
    "tracking number",
    "tracking #",
    "in transit",
    "out for delivery",
    "shipping status",
    "delivery status",
    "shipped",
    "unfulfilled",
)
SHIPPING_DELAY_KEYWORDS = (
    "label created",
    "not shipped",
    "no movement",
    "pre-shipment",
)
RETURN_KEYWORDS = ("return", "returning", "rma")
EXCHANGE_KEYWORDS = ("exchange", "swap")
REFUND_KEYWORDS = ("refund", "refund me", "money back")
CANCEL_ORDER_KEYWORDS = ("cancel my order", "cancel order", "stop shipment")
SUBSCRIPTION_KEYWORDS = ("subscription", "unsubscribe", "cancel subscription")
BILLING_KEYWORDS = (
    "charge",
    "charged",
    "billing",
    "payment",
    "invoice",
    "unauthorized",
)
TECHNICAL_KEYWORDS = (
    "login",
    "log in",
    "sign in",
    "password",
    "site error",
    "website error",
    "app crash",
    "crash",
    "bug",
    "not working",
    "error",
)
CHARGEBACK_KEYWORDS = ("chargeback", "dispute", "bank reversed", "scam")

FRAUD_KEYWORDS = ("fraud",)


@dataclass
class RoutingDecision:
    category: str
    tags: List[str]
    reason: str
    department: str
    intent: str


def extract_customer_message(payload: Dict[str, Any], *, default: str = "") -> str:
    if not isinstance(payload, dict):
        return default

    for key in (
        "customer_message",
        "message",
        "body",
        "text",
        "customer_note",
        "content",
    ):
        value = payload.get(key)
        if value is None:
            continue
        try:
            text = str(value).strip()
        except Exception:
            continue
        if text:
            return text

    return default


def _build_decision(
    intent: str, *, category: str, reason: str, extra_tags: Sequence[str] | None = None
) -> RoutingDecision:
    department = INTENT_TO_DEPARTMENT.get(intent, DEFAULT_DEPARTMENT)
    if department not in DEPARTMENTS:
        department = DEFAULT_DEPARTMENT

    tags: List[str] = [DEFAULT_TAG, f"mw-intent-{intent}"]
    if extra_tags:
        tags.extend([tag for tag in extra_tags if tag])

    return RoutingDecision(
        category=category,
        tags=tags,
        reason=reason,
        department=department,
        intent=intent,
    )


def _contains_any(text: str, keywords: Sequence[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _has_order_number(payload: Dict[str, Any]) -> bool:
    order_number, _ = _extract_order_number_from_payload(payload)
    return bool(order_number)


def classify_routing(payload: Dict[str, Any]) -> RoutingDecision:
    text = extract_customer_message(payload, default="").strip()
    if not text:
        return _build_decision(
            "unknown",
            category="general",
            reason="no customer message provided; default routing applied",
        )

    lowered = text.lower()

    # Check fraud BEFORE chargeback to ensure correct routing
    if _contains_any(lowered, FRAUD_KEYWORDS):
        return _build_decision(
            "fraud_suspected",
            category="escalation",
            reason="matched fraud indicator language",
        )

    if _contains_any(lowered, CHARGEBACK_KEYWORDS):
        return _build_decision(
            "chargeback_dispute",
            category="escalation",
            reason="matched chargeback or dispute language",
        )

    if _contains_any(lowered, TECHNICAL_KEYWORDS):
        return _build_decision(
            "technical_support",
            category="technical",
            reason="matched technical support keyword",
        )

    if _contains_any(lowered, SUBSCRIPTION_KEYWORDS):
        return _build_decision(
            "cancel_subscription",
            category="billing",
            reason="matched subscription cancellation keyword",
        )

    if _contains_any(lowered, BILLING_KEYWORDS):
        return _build_decision(
            "billing_issue",
            category="billing",
            reason="matched billing keyword",
        )

    if _has_order_number(payload) and _contains_any(
        lowered, ORDER_STATUS_CANDIDATE_KEYWORDS
    ):
        return _build_decision(
            "order_status_tracking",
            category="order_status",
            reason="order number present with shipping or tracking language",
        )

    if _contains_any(lowered, EXCHANGE_KEYWORDS):
        return _build_decision(
            "exchange_request",
            category="returns",
            reason="matched exchange keyword",
        )

    if _contains_any(lowered, REFUND_KEYWORDS):
        return _build_decision(
            "refund_request",
            category="returns",
            reason="matched refund keyword",
        )

    if _contains_any(lowered, RETURN_KEYWORDS):
        return _build_decision(
            "return_request",
            category="returns",
            reason="matched return keyword",
        )

    if _contains_any(lowered, CANCEL_ORDER_KEYWORDS):
        return _build_decision(
            "cancel_order",
            category="order_change",
            reason="matched order cancellation keyword",
        )

    if _contains_any(lowered, SHIPPING_DELAY_KEYWORDS):
        return _build_decision(
            "shipping_delay_not_shipped",
            category="order_status",
            reason="matched shipping delay keyword",
        )

    if _contains_any(lowered, ORDER_STATUS_KEYWORDS):
        return _build_decision(
            "order_status_tracking",
            category="order_status",
            reason="matched order status keyword",
        )

    return _build_decision(
        "unknown_other",
        category="general",
        reason="no strong intent keyword detected",
    )
