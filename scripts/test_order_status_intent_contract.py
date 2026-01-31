from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ["MW_OPENAI_INTENT_ENABLED"] = "true"

import backend.tests.test_order_status_intent as backend_intent_tests  # noqa: E402
from richpanel_middleware.automation import (  # noqa: E402
    order_status_intent as intent,
)
from richpanel_middleware.integrations.openai import (  # noqa: E402
    ChatCompletionResponse,
    OpenAIRequestError,
)


class _StubClient:
    def __init__(self, message: str, *, raw: Optional[dict] = None) -> None:
        self.message = message
        self.raw = raw
        self.calls = 0

    def chat_completion(self, request, safe_mode: bool, automation_enabled: bool):  # type: ignore[no-untyped-def]
        self.calls += 1
        return ChatCompletionResponse(
            model=request.model,
            message=self.message,
            status_code=200,
            url="https://example.com",
            raw=self.raw,
            dry_run=False,
        )


class OrderStatusIntentContractTests(unittest.TestCase):
    def test_parse_intent_result_errors(self) -> None:
        result, error = intent.parse_intent_result("")
        self.assertIsNone(result)
        self.assertEqual(error, "empty_response")

        result, error = intent.parse_intent_result("not-json")
        self.assertIsNone(result)
        self.assertEqual(error, "invalid_json")

        result, error = intent.parse_intent_result("[]")
        self.assertIsNone(result)
        self.assertEqual(error, "not_a_dict")

        result, error = intent.parse_intent_result('{"confidence": 0.5}')
        self.assertIsNone(result)
        self.assertEqual(error, "missing_is_order_status")

        result, error = intent.parse_intent_result('{"is_order_status": true}')
        self.assertIsNone(result)
        self.assertEqual(error, "missing_confidence")

        result, error = intent.parse_intent_result(
            '{"is_order_status": true, "confidence": 2, "reason": "x"}'
        )
        self.assertIsNone(result)
        self.assertEqual(error, "confidence_out_of_range")

    def test_parse_intent_result_handles_wrapped_json(self) -> None:
        raw = (
            'prefix {"is_order_status": false, "confidence": 0.2, "reason": "refund", '
            '"extracted_order_number": null, "language": "EN"} suffix'
        )
        result, error = intent.parse_intent_result(raw)
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertFalse(result.is_order_status)
        self.assertEqual(result.language, "en")

    def test_parse_intent_result_fallback_order_number(self) -> None:
        payload = json.dumps(
            {
                "is_order_status": True,
                "confidence": 0.9,
                "reason": "status",
                "extracted_order_number": None,
                "language": "en",
            }
        )
        result, error = intent.parse_intent_result(
            payload, fallback_text="Order #778899"
        )
        self.assertIsNone(error)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.extracted_order_number, "778899")

    def test_normalizers_and_redaction(self) -> None:
        self.assertEqual(intent._coerce_bool("true"), True)
        self.assertEqual(intent._coerce_bool("false"), False)
        self.assertEqual(intent._coerce_bool(1), True)
        self.assertIsNone(intent._coerce_bool("maybe"))

        self.assertEqual(intent._normalize_language("EN-US-longer"), "en-us-longer"[:12])
        self.assertEqual(intent._normalize_order_number("#12345"), "12345")
        self.assertIsNone(intent._normalize_order_number("null"))

        redacted = intent.redact_ticket_text(
            "Hi, I'm John Doe. Email john@example.com. Order #123456. 123 Main St. https://x.io"
        )
        self.assertIsNotNone(redacted)
        assert redacted is not None
        self.assertNotIn("john@example.com", redacted)
        self.assertNotIn("Main St", redacted)
        self.assertNotIn("https://x.io", redacted)
        self.assertIn("123456", redacted)
        self.assertIn("<redacted>", redacted)

    def test_redaction_truncates_long_text(self) -> None:
        text = "Order 12345 " * 50
        redacted = intent.redact_ticket_text(text, max_chars=40)
        self.assertIsNotNone(redacted)
        assert redacted is not None
        self.assertTrue(redacted.endswith("..."))
        self.assertLessEqual(len(redacted), 43)

    def test_response_id_info_variants(self) -> None:
        response = ChatCompletionResponse(
            model="gpt-test",
            message="{}",
            status_code=200,
            url="https://example.com",
            raw={"id": "resp-1"},
        )
        response_id, reason = intent._response_id_info(response)
        self.assertEqual(response_id, "resp-1")
        self.assertIsNone(reason)

        response = ChatCompletionResponse(
            model="gpt-test",
            message="{}",
            status_code=200,
            url="https://example.com",
            raw={},
        )
        response_id, reason = intent._response_id_info(response)
        self.assertIsNone(response_id)
        self.assertEqual(reason, "response_id_missing")

        response = ChatCompletionResponse(
            model="gpt-test",
            message="{}",
            status_code=200,
            url="https://example.com",
            raw=None,
        )
        response_id, reason = intent._response_id_info(response)
        self.assertIsNone(response_id)
        self.assertEqual(reason, "raw_missing")

        response_id, reason = intent._response_id_info(None)
        self.assertIsNone(response_id)
        self.assertEqual(reason, "no_response")

        response = ChatCompletionResponse(
            model="gpt-test",
            message=None,
            status_code=0,
            url="https://example.com",
            raw={},
            dry_run=True,
            reason="dry_run",
        )
        response_id, reason = intent._response_id_info(response)
        self.assertIsNone(response_id)
        self.assertEqual(reason, "dry_run")

    def test_classify_intent_gated(self) -> None:
        artifact = intent.classify_order_status_intent(
            "Where is my order?",
            conversation_id="c-1",
            event_id="e-1",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=True,
        )
        self.assertFalse(artifact.accepted)
        self.assertEqual(artifact.gated_reason, "network_disabled")
        self.assertIsNone(artifact.ticket_excerpt_redacted)

    def test_classify_intent_shadow_disabled(self) -> None:
        os.environ["MW_OPENAI_SHADOW_ENABLED"] = "false"
        artifact = intent.classify_order_status_intent(
            "Where is my order?",
            conversation_id="c-1",
            event_id="e-1",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=False,
        )
        self.assertFalse(artifact.accepted)
        self.assertEqual(artifact.gated_reason, "shadow_disabled")
        os.environ["MW_OPENAI_SHADOW_ENABLED"] = "true"

    def test_classify_intent_accepts_and_rejects(self) -> None:
        payload = json.dumps(
            {
                "is_order_status": True,
                "confidence": 0.9,
                "reason": "status",
                "extracted_order_number": "12345",
                "language": "en",
            }
        )
        client = _StubClient(payload, raw={"id": "resp-test"})
        with mock.patch(
            "richpanel_middleware.automation.order_status_intent.get_confidence_threshold",
            return_value=0.5,
        ):
            artifact = intent.classify_order_status_intent(
                "Where is my order?",
                conversation_id="c-2",
                event_id="e-2",
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                client=client,
            )
        self.assertTrue(artifact.accepted)
        self.assertEqual(artifact.response_id, "resp-test")
        self.assertEqual(client.calls, 1)

    def test_classify_intent_request_failed(self) -> None:
        class _ErrorClient:
            def __init__(self) -> None:
                self.calls = 0

            def chat_completion(self, request, safe_mode: bool, automation_enabled: bool):  # type: ignore[no-untyped-def]
                self.calls += 1
                raise OpenAIRequestError(
                    "boom",
                    response=ChatCompletionResponse(
                        model=request.model,
                        message=None,
                        status_code=500,
                        url="https://example.com",
                        raw={"id": "resp-err"},
                        dry_run=False,
                    ),
                )

        client = _ErrorClient()
        artifact = intent.classify_order_status_intent(
            "Where is my order?",
            conversation_id="c-4",
            event_id="e-4",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(client.calls, 1)
        self.assertEqual(artifact.parse_error, "request_failed")
        self.assertTrue(artifact.llm_called)

        bad_client = _StubClient("not-json", raw={"id": "resp-bad"})
        with mock.patch(
            "richpanel_middleware.automation.order_status_intent.get_confidence_threshold",
            return_value=0.5,
        ):
            artifact = intent.classify_order_status_intent(
                "Where is my order?",
                conversation_id="c-3",
                event_id="e-3",
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                client=bad_client,
            )
        self.assertFalse(artifact.accepted)
        self.assertEqual(artifact.parse_error, "invalid_json")

    def test_backend_order_status_intent_tests(self) -> None:
        backend_intent_tests.test_parse_intent_result_accepts_json()
        backend_intent_tests.test_parse_intent_result_rejects_non_json()
        backend_intent_tests.test_parse_intent_result_extracts_from_wrapped_json()
        backend_intent_tests.test_parse_intent_result_uses_fallback_order_number()
        backend_intent_tests.test_extract_order_number_from_text()
        backend_intent_tests.test_redact_ticket_text_removes_pii()
        backend_intent_tests.test_intent_classification_clearly_order_status()
        backend_intent_tests.test_intent_classification_clearly_not_order_status()
        backend_intent_tests.test_intent_classification_ambiguous_rejected()
        backend_intent_tests.test_intent_classification_rejects_injection_output()


if __name__ == "__main__":
    raise SystemExit(unittest.main())
