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


def test_greeting_enforcement() -> None:
    body = "Thanks for reaching out - here's what we see so far..."
    with_name = pipeline._ensure_order_status_greeting(body, "Sarah")
    assert with_name.startswith("Hi Sarah,\n\n")

    without_name = pipeline._ensure_order_status_greeting(body, None)
    assert without_name.startswith("Hi there,\n\n")


def test_signature_enforcement_idempotent() -> None:
    body = "Thanks for reaching out - here's what we see so far..."
    signed = pipeline._ensure_holly_signature(body)
    assert signed.endswith("Holly\nScentiment Customer Support")

    signed_again = pipeline._ensure_holly_signature(signed)
    assert signed_again == signed
