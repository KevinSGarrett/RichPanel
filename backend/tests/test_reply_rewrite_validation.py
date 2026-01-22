from __future__ import annotations

import json

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
