from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.llm_reply_rewriter import (
    RewriteResult,
    rewrite_order_status_reply,
)
from richpanel_middleware.integrations.openai import ChatCompletionResponse


class _FakeOpenAIClient:
    def __init__(self, response: ChatCompletionResponse):
        self.response = response
        self.calls = 0

    def chat_completion(
        self,
        request,
        *,
        safe_mode: bool,
        automation_enabled: bool,
    ) -> ChatCompletionResponse:
        self.calls += 1
        return self.response


class _FailingOpenAIClient:
    def __init__(self, exc: Exception):
        self.exc = exc
        self.calls = 0

    def chat_completion(self, request, *, safe_mode: bool, automation_enabled: bool):
        self.calls += 1
        raise self.exc


class LLMReplyRewriterTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("OPENAI_REPLY_REWRITE_ENABLED", None)

    def test_rewrite_disabled_is_fail_closed(self) -> None:
        draft = {"body": "Original reply"}
        summary = {"status": "shipped", "id": "ord-123"}

        result = rewrite_order_status_reply(
            draft,
            summary,
            safe_mode=True,
            automation_enabled=False,
            allow_network=False,
            outbound_enabled=False,
        )

        self.assertIsInstance(result, RewriteResult)
        self.assertFalse(result.used_llm)
        self.assertEqual(result.reason, "rewrite_disabled")
        self.assertEqual(result.reply, draft)

    def test_invalid_response_falls_back_to_deterministic(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"

        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message="not-json",
            status_code=200,
            url="http://example.com",
            raw={"choices": [{"message": {"content": "not-json"}}]},
            dry_run=False,
        )
        client = _FakeOpenAIClient(response)

        draft = {"body": "Deterministic reply"}
        summary = {"status": "pending", "id": "ord-456"}

        result = rewrite_order_status_reply(
            draft,
            summary,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )

        self.assertFalse(result.used_llm)
        self.assertEqual(result.reason, "invalid_response")
        self.assertEqual(result.reply, draft)
        self.assertEqual(client.calls, 1)

    def test_rewrite_success_updates_body(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"

        rewritten_body = "Rewritten reply body"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "Rewritten reply body", "confidence": 0.92, "risk_flag": false}',
            status_code=200,
            url="http://example.com",
            raw={"choices": [{"message": {"content": rewritten_body}}]},
            dry_run=False,
        )
        client = _FakeOpenAIClient(response)

        draft = {"body": "Original deterministic reply"}
        summary = {"status": "delivered", "id": "ord-789"}

        result = rewrite_order_status_reply(
            draft,
            summary,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )

        self.assertTrue(result.used_llm)
        self.assertEqual(result.reason, "rewritten")
        self.assertEqual(result.reply["body"], rewritten_body)
        self.assertEqual(result.reply.get("confidence"), 0.92)

    def test_log_record_redacts_pii(self) -> None:
        draft = {"body": "Customer email is ava@example.com"}
        summary = {"status": "shipped", "id": "ord-999"}

        result = rewrite_order_status_reply(
            draft,
            summary,
            safe_mode=True,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=False,
        )

        log_record = result.log_record()
        log_str = json.dumps(log_record)

        self.assertNotIn("ava@example.com", log_str)
        self.assertTrue(log_record["prompt_fingerprint"])


if __name__ == "__main__":
    unittest.main()
