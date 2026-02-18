from __future__ import annotations

from richpanel_middleware.automation.order_status_prompts import (
    OrderStatusReplyContext,
    build_order_status_reply_prompt,
)
from richpanel_middleware.automation import pipeline


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
    assert "customer_message_excerpt" in messages[1].content
    assert "\"customer_first_name\":\"Sarah\"" in messages[1].content
    assert (
        "Where is my order? I'm worried it won't arrive in time."
        in messages[1].content
    )
    assert "Draft reply body" in messages[1].content


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


def test_excerpt_empty_returns_none() -> None:
    assert pipeline._build_customer_message_excerpt("") is None


def test_excerpt_boundary_no_truncation() -> None:
    raw = "x" * pipeline._MAX_CUSTOMER_MESSAGE_EXCERPT_CHARS
    excerpt = pipeline._build_customer_message_excerpt(raw)
    assert excerpt == raw


def test_extract_customer_first_name_from_payload() -> None:
    payload = {
        "customer_profile": {"first_name": "Sarah"},
        "requester": {"firstName": "Sam"},
    }
    assert pipeline._extract_customer_first_name_from_payload(payload) == "Sarah"
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

    loud = "HEY! Thanks for the update."
    loud_replaced = pipeline._ensure_order_status_greeting(loud, "Sarah")
    assert loud_replaced.startswith("Hi Sarah,\n\n")

    leading_blanks = "\n\nHello there,\nBody"
    blanks_replaced = pipeline._ensure_order_status_greeting(leading_blanks, None)
    assert blanks_replaced.startswith("Hi there,\n\n")


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
