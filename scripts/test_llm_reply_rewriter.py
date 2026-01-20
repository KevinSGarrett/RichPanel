from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.llm_reply_rewriter import (  # noqa: E402
    rewrite_reply,
)
from richpanel_middleware.integrations.openai import (  # noqa: E402
    ChatCompletionResponse,
    OpenAIClient,
    OpenAIRequestError,
)


class _FakeClient:
    def __init__(
        self,
        *,
        response: ChatCompletionResponse | None,
        raise_error: bool = False,
    ) -> None:
        self.response = response
        self.raise_error = raise_error
        self.calls = 0

    def chat_completion(self, request, safe_mode: bool, automation_enabled: bool):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.raise_error:
            raise OpenAIRequestError("simulated failure")
        return self.response


def _fake_client(
    *, response: ChatCompletionResponse | None, raise_error: bool = False
) -> _FakeClient:
    return _FakeClient(response=response, raise_error=raise_error)


class ReplyRewriteTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("OPENAI_REPLY_REWRITE_ENABLED", None)

    def test_gates_block_when_disabled(self) -> None:
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "rewritten", "confidence": 0.9}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)
        result = rewrite_reply(
            "deterministic reply",
            conversation_id="t-1",
            event_id="evt-1",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertFalse(result.rewritten)
        self.assertEqual(result.reason, "rewrite_disabled")
        self.assertEqual(result.body, "deterministic reply")
        self.assertEqual(client.calls, 0)

    def test_rewrite_applies_when_enabled_and_safe(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "rewritten response", "confidence": 0.95, "risk_flags": []}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "deterministic reply",
            conversation_id="t-2",
            event_id="evt-2",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertTrue(result.rewritten)
        self.assertEqual(result.body, "rewritten response")
        self.assertEqual(result.reason, "applied")
        self.assertEqual(client.calls, 1)

    def test_gates_block_network(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "rewritten response", "confidence": 0.95}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "deterministic reply",
            conversation_id="t-net",
            event_id="evt-net",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertFalse(result.rewritten)
        self.assertEqual(result.reason, "network_disabled")
        self.assertEqual(result.body, "deterministic reply")
        self.assertEqual(client.calls, 0)

    def test_gates_block_outbound(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "rewritten response", "confidence": 0.95}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "deterministic reply",
            conversation_id="t-outbound",
            event_id="evt-outbound",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=False,
            client=cast(OpenAIClient, client),
        )

        self.assertFalse(result.rewritten)
        self.assertEqual(result.reason, "outbound_disabled")
        self.assertEqual(result.body, "deterministic reply")
        self.assertEqual(client.calls, 0)

    def test_fallback_on_parse_failure_preserves_original(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message="not-json",
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "original body",
            conversation_id="t-3",
            event_id="evt-3",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertFalse(result.rewritten)
        self.assertEqual(result.body, "original body")
        self.assertEqual(result.reason, "invalid_json")

    def test_parse_response_extracts_embedded_json(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='Here is JSON: {"body": "cleaned", "confidence": 0.9, "risk_flags": []}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "original body",
            conversation_id="t-embed",
            event_id="evt-embed",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertTrue(result.rewritten)
        self.assertEqual(result.body, "cleaned")
        self.assertEqual(result.reason, "applied")

    def test_parse_response_brace_inside_string(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message=(
                'Note: {"body": "Hello} there", "confidence": 0.9, "risk_flags": []}'
            ),
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "original body",
            conversation_id="t-brace",
            event_id="evt-brace",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertTrue(result.rewritten)
        self.assertEqual(result.body, "Hello} there")
        self.assertEqual(result.reason, "applied")

    def test_response_id_reason_set_when_raw_empty(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "rewritten", "confidence": 0.9, "risk_flags": []}',
            status_code=200,
            url="https://example.com",
            raw={},
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "original body",
            conversation_id="t-raw",
            event_id="evt-raw",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertEqual(result.response_id_unavailable_reason, "response_id_missing")

    def test_fallback_on_low_confidence_preserves_original(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "maybe", "confidence": 0.2}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)

        result = rewrite_reply(
            "original body",
            conversation_id="t-low",
            event_id="evt-low",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertFalse(result.rewritten)
        self.assertEqual(result.body, "original body")
        self.assertEqual(result.reason, "low_confidence")

    def test_no_response_returns_fallback(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        client = _fake_client(response=None)

        result = rewrite_reply(
            "original body",
            conversation_id="t-none",
            event_id="evt-none",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=cast(OpenAIClient, client),
        )

        self.assertFalse(result.rewritten)
        self.assertEqual(result.reason, "no_response")

    def test_logs_do_not_include_body(self) -> None:
        os.environ["OPENAI_REPLY_REWRITE_ENABLED"] = "true"
        response = ChatCompletionResponse(
            model="gpt-5.2-chat-latest",
            message='{"body": "safe text", "confidence": 0.9}',
            status_code=200,
            url="https://example.com",
        )
        client = _fake_client(response=response)
        reply_body = "Sensitive customer info 12345"

        with self.assertLogs(
            "richpanel_middleware.automation.llm_reply_rewriter", level="INFO"
        ) as captured:
            result = rewrite_reply(
                reply_body,
                conversation_id="t-4",
                event_id="evt-4",
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                client=cast(OpenAIClient, client),
            )

        combined_logs = " ".join(captured.output)
        self.assertNotIn(reply_body, combined_logs)
        self.assertTrue(result.fingerprint)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReplyRewriteTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
