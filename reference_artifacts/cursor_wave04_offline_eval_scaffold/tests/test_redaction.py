from mw_llm.redaction import redact_text, contains_order_number, contains_tracking_number


def test_redact_text_masks_pii():
    text = "Email me at customer@example.com or call +1 (555) 123-4567 about order #12345."
    result = redact_text(text)
    assert "[REDACTED_EMAIL]" in result.redacted_text
    assert "[REDACTED_PHONE]" in result.redacted_text
    assert "[REDACTED_ORDER]" in result.redacted_text
    assert "customer@example.com" in result.matches["email"][0]


def test_contains_helpers():
    assert contains_order_number("order #123456")
    assert contains_tracking_number("1Z999AA10123456784")
