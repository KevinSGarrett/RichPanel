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
    assert "Never mention AI, bots, automation, templates" in messages[0].content
    assert "Do NOT encourage inbound contact" in messages[0].content
    assert "\"reply back\"" in messages[0].content
    assert "ONE concrete anchor detail" in messages[0].content
    assert "Do NOT output a \"Key Details\" title" in messages[0].content
    assert "delivery date ranges" in messages[0].content
    assert "\"message us\"" in messages[0].content
    assert "\"get back to us\"" in messages[0].content
    assert "\"if you have questions\"" in messages[0].content
    assert "customer_message_excerpt" in messages[1].content
    assert "\"customer_first_name\":\"Sarah\"" in messages[1].content
    assert (
        "Where is my order? I'm worried it won't arrive in time."
        in messages[1].content
    )
    assert "Draft reply body" in messages[1].content


def test_prompt_includes_required_verbatim_tokens_from_draft() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = (
        "Delivery is estimated for April 10–April 20, 2026 "
        "(about 49–59 days from today)."
    )
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "Required Verbatim Tokens" in user_content
    assert "- 49–59 days" in user_content
    assert "- April 10–April 20, 2026" in user_content


def test_prompt_omits_required_verbatim_section_without_tokens() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = "We will follow up with an update soon."
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "Required Verbatim Tokens" not in user_content


def test_prompt_includes_verbatim_tokens_with_unicode_dashes() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = (
        "Delivery is estimated for April 10—April 20, 2026 "
        "(about 49–59 days from today)."
    )
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "- April 10—April 20, 2026" in user_content
    assert "- 49–59 days" in user_content


def test_prompt_includes_eta_window_with_em_dash() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = "Delivery should arrive in about 49—59 days."
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "- 49—59 days" in user_content


def test_prompt_includes_single_day_eta_token() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = "Processing typically takes 5 business days."
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "- 5 business days" in user_content


def test_prompt_eta_overlap_prefers_range_only() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = "Processing typically takes 3-5 business days."
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "- 3-5 business days" in user_content
    assert "- 5 business days" not in user_content


def test_prompt_omits_required_verbatim_section_for_empty_draft() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    messages = build_order_status_reply_prompt(
        context=context, draft_reply="", language="en"
    )
    user_content = messages[1].content
    assert "Required Verbatim Tokens" not in user_content


def test_prompt_sanitizes_verbatim_tokens() -> None:
    context = OrderStatusReplyContext(customer_first_name="Sarah")
    draft = "Delivery is estimated for April 10–April 20, 2026.\n(about 49–59 days)"
    messages = build_order_status_reply_prompt(
        context=context, draft_reply=draft, language="en"
    )
    user_content = messages[1].content
    assert "- April 10–April 20, 2026" in user_content
    assert "- 49–59 days" in user_content


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
    blocked_phrases = [
        "feel free to reply",
        "reply back",
        "reply here",
        "reach out",
        "contact us",
        "let us know",
        "message us",
        "get back to us",
        "if you have questions",
        "if you have any questions",
        "if you have any other questions",
    ]
    for phrase in blocked_phrases:
        rewritten = (
            "We are on it and reviewing the latest order details now. "
            "We'll share the next update as soon as it is ready. "
            f"Please {phrase} if anything changes."
        )
        updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
        assert blocked is True
        assert updated != draft
        assert "We are on it and reviewing the latest order details now." in updated
        assert "We'll share the next update as soon as it is ready." in updated
        assert phrase not in updated.lower()

    rewritten_only = "Please reply here if anything changes."
    updated_only, blocked_only = pipeline._apply_inbound_cta_guard(
        rewritten_only, draft
    )
    assert blocked_only is True
    assert updated_only == draft

    safe = "Tracking will be emailed automatically once it ships and is scanned by the carrier."
    updated_safe, blocked_safe = pipeline._apply_inbound_cta_guard(safe, draft)
    assert blocked_safe is False
    assert updated_safe == safe


def test_inbound_cta_guard_boundary_threshold() -> None:
    draft = "Deterministic draft reply."
    base = "We are reviewing the latest details now. We'll share the next update soon."
    cta = "Please reply here if anything changes."
    rewritten = f"{base} {cta}"
    updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
    assert blocked is True
    assert updated == base


def test_inbound_cta_guard_fallback_when_mostly_cta() -> None:
    draft = "Deterministic draft reply."
    rewritten = (
        "Order is processing. "
        "Please reply back if you have any questions or need anything else at all."
    )
    updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
    assert blocked is True
    assert updated == draft


def test_inbound_cta_guard_removes_multiple_cta_sentences_across_paragraphs() -> None:
    draft = "Deterministic draft reply."
    para1 = "Thanks for your patience. Please reply back if anything changes."
    para2 = "We are preparing your order. If you have any questions, let us know."
    rewritten = f"{para1}\n\n{para2}"
    updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
    assert blocked is True
    assert "Please reply back" not in updated
    assert "If you have any questions" not in updated
    assert "Thanks for your patience." in updated
    assert "We are preparing your order." in updated
    assert "\n\n" in updated


def test_inbound_cta_guard_preserves_non_cta_paragraphs() -> None:
    draft = "Deterministic draft reply."
    para1 = "We are reviewing the latest details now."
    para2 = "Please reply here if anything changes."
    para3 = "We'll share the next update as soon as it is ready."
    rewritten = f"{para1}\n\n{para2}\n\n{para3}"
    updated, blocked = pipeline._apply_inbound_cta_guard(rewritten, draft)
    assert blocked is True
    assert para2.lower() not in updated.lower()
    assert para1 in updated
    assert para3 in updated


def test_shipping_method_window_stripped_in_context() -> None:
    payload = {"message": "Where is my order?"}
    delivery_estimate = {
        "eta_human": "1-3 business days",
        "normalized_method": "Standard (3–7 business days)",
    }
    order_summary = {"shipping_method_name": "Standard (3–7 business days)"}
    context = pipeline._build_order_status_reply_context(
        payload=payload,
        draft_reply={},
        delivery_estimate=delivery_estimate,
        order_summary=order_summary,
    )
    assert context.shipping_method == "Standard"


def test_shipping_method_window_does_not_strip_descriptive_day() -> None:
    payload = {"message": "Where is my order?"}
    delivery_estimate = {
        "eta_human": "1-3 business days",
        "normalized_method": "Express (Next Day)",
    }
    order_summary = {"shipping_method_name": "Express (Next Day)"}
    context = pipeline._build_order_status_reply_context(
        payload=payload,
        draft_reply={},
        delivery_estimate=delivery_estimate,
        order_summary=order_summary,
    )
    assert context.shipping_method == "Express (Next Day)"


def test_shipping_method_window_does_not_strip_descriptive_day_delivery() -> None:
    payload = {"message": "Where is my order?"}
    delivery_estimate = {
        "eta_human": "1-3 business days",
        "normalized_method": "Express (Next Day Delivery)",
    }
    order_summary = {"shipping_method_name": "Express (Next Day Delivery)"}
    context = pipeline._build_order_status_reply_context(
        payload=payload,
        draft_reply={},
        delivery_estimate=delivery_estimate,
        order_summary=order_summary,
    )
    assert context.shipping_method == "Express (Next Day Delivery)"


def test_strip_shipping_method_window_priority_two_day() -> None:
    assert pipeline._strip_shipping_method_window("Priority (2-Day)") == "Priority"


def test_strip_shipping_method_window_none_or_empty() -> None:
    assert pipeline._strip_shipping_method_window(None) is None
    assert pipeline._strip_shipping_method_window("") == ""



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


class OrderStatusReplyPersonalizationCoverageTests(unittest.TestCase):
    def test_unittest_adapter_inbound_cta_guard_boundary(self) -> None:
        test_inbound_cta_guard_boundary_threshold()

    def test_unittest_adapter_inbound_cta_guard_fallback(self) -> None:
        test_inbound_cta_guard_fallback_when_mostly_cta()

    def test_unittest_adapter_inbound_cta_guard_multi_paragraph(self) -> None:
        test_inbound_cta_guard_removes_multiple_cta_sentences_across_paragraphs()

    def test_unittest_adapter_shipping_method_descriptive_day_delivery(self) -> None:
        test_shipping_method_window_does_not_strip_descriptive_day_delivery()

    def test_unittest_adapter_shipping_method_priority_two_day(self) -> None:
        test_strip_shipping_method_window_priority_two_day()

    def test_unittest_adapter_shipping_method_none_or_empty(self) -> None:
        test_strip_shipping_method_window_none_or_empty()


class OrderStatusReplyPersonalizationUnittestAdapter(unittest.TestCase):
    def test_execute_pytest_style_functions(self) -> None:
        test_prompt_includes_excerpt_and_first_name()
        test_prompt_includes_required_verbatim_tokens_from_draft()
        test_prompt_omits_required_verbatim_section_without_tokens()
        test_prompt_includes_verbatim_tokens_with_unicode_dashes()
        test_prompt_includes_eta_window_with_em_dash()
        test_prompt_includes_single_day_eta_token()
        test_prompt_eta_overlap_prefers_range_only()
        test_prompt_omits_required_verbatim_section_for_empty_draft()
        test_prompt_sanitizes_verbatim_tokens()
        test_reply_context_payload_excludes_none()
        test_build_order_status_reply_context()
        test_excerpt_is_sanitized_and_truncated()
        test_excerpt_empty_returns_none()
        test_excerpt_boundary_no_truncation()
        test_extract_customer_first_name_from_payload()
        test_extract_customer_first_name_from_order_summary()
        test_inbound_cta_guard_reverts_to_draft()
        test_inbound_cta_guard_boundary_threshold()
        test_inbound_cta_guard_fallback_when_mostly_cta()
        test_inbound_cta_guard_removes_multiple_cta_sentences_across_paragraphs()
        test_inbound_cta_guard_preserves_non_cta_paragraphs()
        test_shipping_method_window_stripped_in_context()
        test_shipping_method_window_does_not_strip_descriptive_day()
        test_shipping_method_window_does_not_strip_descriptive_day_delivery()
        test_strip_shipping_method_window_priority_two_day()
        test_strip_shipping_method_window_none_or_empty()
        test_greeting_enforcement()
        test_signature_enforcement_idempotent()


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
