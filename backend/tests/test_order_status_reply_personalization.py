from __future__ import annotations

from richpanel_middleware.automation.order_status_prompts import (
    OrderStatusReplyContext,
    build_order_status_reply_prompt,
)
from richpanel_middleware.automation import pipeline
import unittest


def test_prompt_includes_excerpt_and_first_name() -> None:
    context = OrderStatusReplyContext(
        customer_first_name="Sarah",
        customer_message_excerpt=(
            "Where is my order? I'm worried it won't arrive in time."
        ),
        tracking_number="1Z999AA10123456784",
    )
    messages = build_order_status_reply_prompt(
        context=context, draft_reply="Draft reply body", language="en"
    )

    assert messages[0].role == "system"
    assert "Do not mention AI, bot, automation, or templates." in messages[0].content
    assert "Do NOT encourage inbound contact" in messages[0].content
    assert "\"reply back\"" in messages[0].content
    assert "customer_message_excerpt" in messages[1].content
    assert "\"customer_first_name\":\"Sarah\"" in messages[1].content
    assert (
        "Where is my order? I'm worried it won't arrive in time."
        in messages[1].content
    )
    assert "Draft reply body" in messages[1].content


def test_reply_context_payload_excludes_none() -> None:
    context = OrderStatusReplyContext(tracking_number="123", carrier=None)
    payload = context.as_payload()
    assert payload["tracking_number"] == "123"
    assert "carrier" not in payload


def test_build_order_status_reply_context() -> None:
    payload = {"first_name": "Sarah", "message": "Where is my order?"}
    draft_reply = {
        "tracking_number": "1Z999AA10123456784",
        "tracking_url": "https://tracking.example.com/track/1Z999AA10123456784",
        "carrier": "UPS",
    }
    delivery_estimate = {"eta_human": "1-3 business days", "normalized_method": "ground"}
    order_summary = {"shipping_method_name": "Ground"}
    context = pipeline._build_order_status_reply_context(
        payload=payload,
        draft_reply=draft_reply,
        delivery_estimate=delivery_estimate,
        order_summary=order_summary,
    )
    assert context.customer_first_name == "Sarah"
    assert context.customer_message_excerpt == "Where is my order?"
    assert context.eta_window == "1-3 business days"
    assert context.tracking_number == "1Z999AA10123456784"

    context_fallback = pipeline._build_order_status_reply_context(
        payload=payload,
        draft_reply={},
        delivery_estimate=None,
        order_summary={"shipping_method": "Postal"},
    )
    assert context_fallback.shipping_method is not None

    context_shipping = pipeline._build_order_status_reply_context(
        payload=payload,
        draft_reply={},
        delivery_estimate={"eta_human": "2-4 days"},
        order_summary={"shipping_method_name": "Ground"},
    )
    assert context_shipping.shipping_method is not None


def test_excerpt_is_sanitized_and_truncated() -> None:
    raw = (
        "Email me at sarah@example.com or call 555-123-4567. "
        "Tracking link: https://tracking.example.com/track/ABC123 "
        + "x" * 800
    )
    excerpt = pipeline._build_customer_message_excerpt(raw)

    assert excerpt is not None
    assert "<redacted>" in excerpt
    assert "sarah@example.com" not in excerpt
    assert "https://tracking.example.com/track/ABC123" not in excerpt
    assert len(excerpt) <= pipeline._MAX_CUSTOMER_MESSAGE_EXCERPT_CHARS
    assert excerpt.endswith("x")


def test_excerpt_empty_returns_none() -> None:
    assert pipeline._build_customer_message_excerpt("") is None
    assert pipeline._build_customer_message_excerpt("   ") is None


def test_excerpt_boundary_no_truncation() -> None:
    raw = "x" * pipeline._MAX_CUSTOMER_MESSAGE_EXCERPT_CHARS
    excerpt = pipeline._build_customer_message_excerpt(raw)
    assert excerpt == raw

    long_raw = "y" * (pipeline._MAX_CUSTOMER_MESSAGE_EXCERPT_CHARS + 10)
    long_excerpt = pipeline._build_customer_message_excerpt(long_raw)
    assert long_excerpt == "y" * pipeline._MAX_CUSTOMER_MESSAGE_EXCERPT_CHARS


def test_extract_customer_first_name_from_payload() -> None:
    class _BadStr:
        def __str__(self) -> str:
            raise ValueError("boom")

    payload = {
        "customer_profile": {"first_name": "Sarah"},
        "requester": {"firstName": "Sam"},
    }
    assert pipeline._extract_customer_first_name_from_payload(payload) == "Sarah"
    assert pipeline._extract_customer_first_name_from_payload("not-a-dict") is None
    assert pipeline._extract_customer_first_name_from_payload({"first_name": _BadStr()}) is None
    assert (
        pipeline._extract_customer_first_name_from_payload({"firstName": "O'Neil"})
        == "O'Neil"
    )
    assert (
        pipeline._extract_customer_first_name_from_payload({"firstName": "Mary2"})
        is None
    )
    assert pipeline._extract_customer_first_name_from_payload({"first_name": "  "}) is None
    assert pipeline._extract_customer_first_name_from_payload({"first_name": "1234"}) is None
    assert (
        pipeline._extract_customer_first_name_from_payload({"first_name": "A" * 65})
        is None
    )


def test_extract_customer_first_name_from_order_summary() -> None:
    assert (
        pipeline._extract_customer_first_name({}, {"customer_first_name": "Sarah"})
        == "Sarah"
    )
    assert (
        pipeline._extract_customer_first_name({}, {"customer_name": "Jane Doe"}) == "Jane"
    )
    assert (
        pipeline._extract_customer_first_name({}, {"shipping_address_name": "Sam Smith"})
        == "Sam"
    )
    assert (
        pipeline._extract_customer_first_name({}, {"customer_first_name": "1234"}) is None
    )


def test_inbound_cta_guard_reverts_to_draft() -> None:
    draft = "Deterministic draft reply."
    rewritten = "Feel free to reply if you have questions."
    updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
    assert blocked is True
    assert updated == draft

    safe = "Tracking will be emailed automatically once it ships and is scanned by the carrier."
    updated_safe, blocked_safe = pipeline._apply_inbound_cta_guard(safe, draft)
    assert blocked_safe is False
    assert updated_safe == safe


def test_inbound_cta_guard_case_insensitive_and_non_match() -> None:
    draft = "Deterministic draft reply."
    rewritten = "Please Reply Back if you need more details."
    updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
    assert blocked is True
    assert updated == draft

    assert pipeline._contains_inbound_cta("Contactless delivery is used.") is False


def test_inbound_cta_guard_all_phrases_detected() -> None:
    phrases = [
        "feel free to reply",
        "reply back",
        "reply here",
        "reach out",
        "contact us",
        "let us know",
        "please reply",
        "email us",
        "call us",
        "contact support",
        "our support team",
        "we're here to help",
        "we are here to help",
    ]
    for phrase in phrases:
        assert pipeline._contains_inbound_cta(phrase.upper()) is True


def test_order_summary_name_fallbacks() -> None:
    summary = {"customer": {"first_name": "Nina"}}
    assert pipeline._extract_customer_first_name(None, summary) == "Nina"

    summary = {"customer": {"firstName": "Uma"}}
    assert pipeline._extract_customer_first_name(None, summary) == "Uma"

    summary = {"customer_name": "Quinn Harper"}
    assert pipeline._extract_customer_first_name(None, summary) == "Quinn"

    summary = {"shipping_address_name": "Sam Doe"}
    assert pipeline._extract_customer_first_name(None, summary) == "Sam"

    summary = {"customer_first_name": "   "}
    assert pipeline._extract_customer_first_name(None, summary) is None
def test_greeting_enforcement() -> None:
    body = "Thanks for reaching out - here's what we see so far..."
    with_name = pipeline._ensure_order_status_greeting(body, "Sarah")
    assert with_name.startswith("Hi Sarah,\n\n")

    without_name = pipeline._ensure_order_status_greeting(body, None)
    assert without_name.startswith("Hi there,\n\n")

    existing = "Hello team,\n\nHere is the update."
    replaced = pipeline._ensure_order_status_greeting(existing, "Sarah")
    assert replaced.startswith("Hi Sarah,\n\n")

    empty = pipeline._ensure_order_status_greeting("", "Sarah")
    assert empty.startswith("Hi Sarah,\n\n")

    inline = "Hi Sarah, your order is on the way."
    inline_replaced = pipeline._ensure_order_status_greeting(inline, "Sarah")
    assert inline_replaced.startswith("Hi Sarah,\n\n")
    assert "your order is on the way." in inline_replaced

    remainder_with_next = "Hi there, status update line\nNext line"
    remainder_wrapped = pipeline._ensure_order_status_greeting(remainder_with_next, None)
    assert remainder_wrapped.startswith("Hi there,\n\n")
    assert "status update line" in remainder_wrapped

    loud = "HEY! Thanks for the update."
    loud_replaced = pipeline._ensure_order_status_greeting(loud, "Sarah")
    assert loud_replaced.startswith("Hi Sarah,\n\n")

    leading_blanks = "\n\nHello there,\nBody"
    blanks_replaced = pipeline._ensure_order_status_greeting(leading_blanks, None)
    assert blanks_replaced.startswith("Hi there,\n\n")

    no_greeting = "Status update\n\nNext line"
    no_greeting_wrapped = pipeline._ensure_order_status_greeting(no_greeting, None)
    assert no_greeting_wrapped.startswith("Hi there,\n\n")
    assert "\n\n\n" not in no_greeting_wrapped

    no_greeting_single = "Status update"
    no_greeting_single_wrapped = pipeline._ensure_order_status_greeting(
        no_greeting_single, None
    )
    assert no_greeting_single_wrapped.startswith("Hi there,\n\n")

    no_greeting_two = "Status update\nNext line"
    no_greeting_two_wrapped = pipeline._ensure_order_status_greeting(
        no_greeting_two, None
    )
    assert no_greeting_two_wrapped.startswith("Hi there,\n\n")

    already_spaced = "Hi there,\n\nBody line"
    already_spaced_wrapped = pipeline._ensure_order_status_greeting(already_spaced, None)
    assert already_spaced_wrapped.startswith("Hi there,\n\n")

    greeting_only = "Hey,"
    greeting_only_wrapped = pipeline._ensure_order_status_greeting(greeting_only, "Sarah")
    assert greeting_only_wrapped == "Hi Sarah,\n\n"

    greeting_with_blank = "Hi there,\n\nBody"
    greeting_with_blank_wrapped = pipeline._ensure_order_status_greeting(
        greeting_with_blank, None
    )
    assert greeting_with_blank_wrapped.startswith("Hi there,\n\n")

    greeting_single = "Hi there,\nBody"
    greeting_single_wrapped = pipeline._ensure_order_status_greeting(
        greeting_single, None
    )
    assert greeting_single_wrapped.startswith("Hi there,\n\n")

    greeting_short = "Hi,\nBody"
    greeting_short_wrapped = pipeline._ensure_order_status_greeting(
        greeting_short, None
    )
    assert greeting_short_wrapped.startswith("Hi there,\n\n")


def test_signature_enforcement_idempotent() -> None:
    body = "Thanks for reaching out - here's what we see so far..."
    signed = pipeline._ensure_holly_signature(body)
    assert signed.endswith("Holly\nScentiment Customer Support")

    signed_again = pipeline._ensure_holly_signature(signed)
    assert signed_again == signed

    trailing = signed + "\n\n"
    assert pipeline._ensure_holly_signature(trailing) == signed

    partial = "Update\n\nHolly"
    assert pipeline._ensure_holly_signature(partial).endswith(
        "Holly\nScentiment Customer Support"
    )

    partial_two = "Update\n\nHolly\nScentiment"
    assert pipeline._ensure_holly_signature(partial_two).endswith(
        "Holly\nScentiment Customer Support"
    )

    partial_support = "Update\n\nScentiment Customer Support"
    assert pipeline._ensure_holly_signature(partial_support).endswith(
        "Holly\nScentiment Customer Support"
    )

    empty_body = ""
    assert pipeline._ensure_holly_signature(empty_body) == "Holly\nScentiment Customer Support"

    with_body = "Update"
    assert pipeline._ensure_holly_signature(with_body).endswith(
        "Holly\nScentiment Customer Support"
    )


class OrderStatusReplyPersonalizationTests(unittest.TestCase):
    def test_prompt_includes_excerpt_and_first_name(self) -> None:
        test_prompt_includes_excerpt_and_first_name()

    def test_reply_context_payload_excludes_none(self) -> None:
        test_reply_context_payload_excludes_none()

    def test_build_order_status_reply_context(self) -> None:
        test_build_order_status_reply_context()

    def test_excerpt_is_sanitized_and_truncated(self) -> None:
        test_excerpt_is_sanitized_and_truncated()

    def test_excerpt_empty_returns_none(self) -> None:
        test_excerpt_empty_returns_none()

    def test_excerpt_boundary_no_truncation(self) -> None:
        test_excerpt_boundary_no_truncation()

    def test_extract_customer_first_name_from_payload(self) -> None:
        test_extract_customer_first_name_from_payload()

    def test_extract_customer_first_name_from_order_summary(self) -> None:
        test_extract_customer_first_name_from_order_summary()

    def test_inbound_cta_guard_reverts_to_draft(self) -> None:
        test_inbound_cta_guard_reverts_to_draft()

    def test_greeting_enforcement(self) -> None:
        test_greeting_enforcement()

    def test_signature_enforcement_idempotent(self) -> None:
        test_signature_enforcement_idempotent()
