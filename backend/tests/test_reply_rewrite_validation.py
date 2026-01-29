from __future__ import annotations

import json

from richpanel_middleware.automation import llm_reply_rewriter as rewriter
from richpanel_middleware.automation.llm_reply_rewriter import rewrite_reply
from richpanel_middleware.integrations.openai import ChatCompletionResponse


class _StubClient:
    def __init__(self, response: ChatCompletionResponse) -> None:
        self.response = response
        self.called = False

    def chat_completion(self, request, *, safe_mode: bool, automation_enabled: bool):
        self.called = True
        return self.response


def _response(body: str, confidence: float = 0.99) -> ChatCompletionResponse:
    message = json.dumps(
        {"body": body, "confidence": confidence, "risk_flags": []}
    )
    return ChatCompletionResponse(
        model="gpt-5.2-chat-latest",
        message=message,
        status_code=200,
        url="https://api.openai.com/v1/chat/completions",
        raw={"id": "resp_test"},
        dry_run=False,
    )


def test_rewrite_rejects_missing_tracking_url() -> None:
    draft = (
        "Thanks for reaching out. Here is the latest tracking information:\n\n"
        "- Carrier: UPS\n"
        "- Tracking number: 1Z999AA10123456784\n"
        "- Tracking link: https://www.ups.com/track?loc=en_US&tracknum=1Z999AA10123456784\n"
    )
    client = _StubClient(_response("Tracking number: 1Z999AA10123456784"))

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert client.called
    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "missing_required_urls"


def test_rewrite_rejects_modified_url() -> None:
    draft = (
        "Tracking link: https://example.com/track/ABC123\n"
        "Let us know if you have any questions."
    )
    client = _StubClient(
        _response("Tracking link: https://example.com/track/ABC123XYZ")
    )

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "missing_required_tokens"


def test_rewrite_rejects_missing_tracking_number() -> None:
    draft = (
        "Tracking details:\n"
        "- Tracking number: ZX98765\n"
        "- Tracking link: https://tracking.example.com/track/OTHER123\n"
    )
    client = _StubClient(
        _response("Tracking link: https://tracking.example.com/track/OTHER123")
    )

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "missing_required_tracking"


def test_rewrite_applies_when_tokens_preserved() -> None:
    draft = (
        "Tracking details:\n"
        "- Tracking number: 1Z999AA10123456784\n"
        "- Tracking link: https://tracking.example.com/track/1Z999AA10123456784\n"
    )
    rewritten = (
        "Here is your tracking info:\n"
        "Tracking number: 1Z999AA10123456784\n"
        "Tracking link: https://tracking.example.com/track/1Z999AA10123456784"
    )
    client = _StubClient(_response(rewritten))

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is True
    assert result.body == rewritten


def test_extract_urls_and_tracking_tokens() -> None:
    text = (
        "Track it here: https://www.ups.com/track?loc=en_US&tracknum=1Z999AA10123456784, "
        "or use tracking number: 1Z999AA10123456784."
    )
    urls = rewriter._extract_urls(text)
    assert urls == [
        "https://www.ups.com/track?loc=en_US&tracknum=1Z999AA10123456784"
    ]
    tokens = rewriter._extract_tracking_tokens(text)
    assert tokens.count("1Z999AA10123456784") == 1


def test_missing_required_tokens_detects_missing_values() -> None:
    original = (
        "Tracking link: https://tracking.example.com/track/ABC123 "
        "Tracking number: ABC123"
    )
    missing_urls, missing_tracking, missing_eta = rewriter._missing_required_tokens(
        original, "Thanks for reaching out."
    )
    assert missing_urls == ["https://tracking.example.com/track/ABC123"]
    assert missing_tracking == ["ABC123"]
    assert missing_eta == []

    missing_urls, missing_tracking, missing_eta = rewriter._missing_required_tokens(
        "Tracking number: ZX98765", "Tracking number: ZX98765"
    )
    assert missing_urls == []
    assert missing_tracking == []
    assert missing_eta == []


def test_rewrite_rejects_modified_eta_window() -> None:
    draft = "It should arrive in about 1-3 business days."
    client = _StubClient(_response("It should arrive in about 2-4 business days."))

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "missing_required_eta"


def test_rewrite_accepts_equivalent_eta_separator() -> None:
    draft = "It should arrive in about 1–3 business days."
    client = _StubClient(_response("It should arrive in about 1-3 business days."))

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is True
    assert result.body == "It should arrive in about 1-3 business days."


def test_rewrite_rejects_unexpected_url() -> None:
    draft = "Thanks for your patience. We'll update you soon."
    client = _StubClient(
        _response("Track it here: https://tracking.example.com/track/ABC123")
    )

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "unexpected_tokens"


def test_rewrite_rejects_unexpected_tracking_number() -> None:
    draft = "Tracking number: ABC123"
    client = _StubClient(
        _response("Tracking number: ABC123. Tracking number: XYZ999.")
    )

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "unexpected_tracking"


def test_rewrite_rejects_internal_tags() -> None:
    draft = "Thanks for your patience. We'll take a look."
    client = _StubClient(
        _response("We updated your request. Tag: mw-order-status-answered.")
    )

    result = rewrite_reply(
        draft,
        conversation_id="conv-test",
        event_id="evt-test",
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
        outbound_enabled=True,
        rewrite_enabled=True,
        client=client,
    )

    assert result.rewritten is False
    assert result.body == draft
    assert result.reason == "contains_internal_tags"