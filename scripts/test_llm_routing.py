#!/usr/bin/env python3
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "local-idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/local/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/local/automation_enabled")
os.environ.setdefault("CONVERSATION_STATE_TABLE_NAME", "local-conversation-state")
os.environ.setdefault("AUDIT_TRAIL_TABLE_NAME", "local-audit-trail")

from richpanel_middleware.automation.llm_routing import (  # noqa: E402
    DEFAULT_CONFIDENCE_THRESHOLD,
    LLMRoutingSuggestion,
    OPENAI_ROUTING_PRIMARY_DEFAULT,
    compute_dual_routing,
    get_confidence_threshold,
    get_openai_routing_primary,
    suggest_llm_routing,
)
from integrations.openai.client import ChatCompletionResponse  # noqa: E402


class MockOpenAIClient:
    def __init__(self, *, response_json=None, dry_run=False):
        self.response_json = response_json or {}
        self.dry_run = dry_run
        self.call_count = 0

    def chat_completion(self, request, *, safe_mode, automation_enabled):
        self.call_count += 1
        if self.dry_run or safe_mode or not automation_enabled:
            return ChatCompletionResponse(
                model=request.model,
                message=None,
                status_code=0,
                url="test",
                raw={"reason": "dry_run"},
                dry_run=True,
                reason="dry_run",
            )
        return ChatCompletionResponse(
            model=request.model,
            message=json.dumps(self.response_json),
            status_code=200,
            url="test",
            raw=self.response_json,
            dry_run=False,
        )


class GatingTests(unittest.TestCase):
    def test_gating_blocks_safe_mode(self):
        client = MockOpenAIClient()
        suggestion = suggest_llm_routing(
            customer_message="test",
            conversation_id="c",
            event_id="e",
            safe_mode=True,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(client.call_count, 0)
        self.assertEqual(suggestion.gated_reason, "safe_mode")

    def test_gating_blocks_automation_disabled(self):
        client = MockOpenAIClient()
        suggestion = suggest_llm_routing(
            customer_message="test",
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=False,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(client.call_count, 0)
        self.assertEqual(suggestion.gated_reason, "automation_disabled")

    def test_gating_blocks_network_disabled(self):
        client = MockOpenAIClient()
        suggestion = suggest_llm_routing(
            customer_message="test",
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(client.call_count, 0)
        self.assertEqual(suggestion.gated_reason, "network_disabled")

    def test_gating_allows_all_enabled(self):
        client = MockOpenAIClient(
            response_json={
                "intent": "order_status_tracking",
                "department": "Email Support Team",
                "confidence": 0.95,
            }
        )
        suggestion = suggest_llm_routing(
            customer_message="test",
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(client.call_count, 1)
        self.assertIsNone(suggestion.gated_reason)


class ArtifactTests(unittest.TestCase):
    def test_artifact_contains_deterministic(self):
        client = MockOpenAIClient(dry_run=True)
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "Where is my order?"},
            conversation_id="c",
            event_id="e",
            safe_mode=True,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=False,
            client=client,
        )
        self.assertIn("intent", artifact.deterministic)

    def test_artifact_serializable(self):
        client = MockOpenAIClient(dry_run=True)
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "test"},
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=False,
            client=client,
        )
        self.assertIsInstance(json.dumps(artifact.to_dict()), str)


class PrimaryFlagTests(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("OPENAI_ROUTING_PRIMARY", None)

    def tearDown(self):
        if self._orig is not None:
            os.environ["OPENAI_ROUTING_PRIMARY"] = self._orig
        else:
            os.environ.pop("OPENAI_ROUTING_PRIMARY", None)

    def test_default_is_false(self):
        self.assertFalse(OPENAI_ROUTING_PRIMARY_DEFAULT)
        self.assertFalse(get_openai_routing_primary())

    def test_default_uses_deterministic(self):
        client = MockOpenAIClient(
            response_json={
                "intent": "refund_request",
                "department": "Returns Admin",
                "confidence": 0.99,
            }
        )
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "Where is my order?"},
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(artifact.primary_source, "deterministic")


class PrimaryFlagOnTests(unittest.TestCase):
    def setUp(self):
        self._orig_p = os.environ.get("OPENAI_ROUTING_PRIMARY")
        self._orig_t = os.environ.get("OPENAI_ROUTING_CONFIDENCE_THRESHOLD")
        os.environ["OPENAI_ROUTING_PRIMARY"] = "true"

    def tearDown(self):
        if self._orig_p:
            os.environ["OPENAI_ROUTING_PRIMARY"] = self._orig_p
        else:
            os.environ.pop("OPENAI_ROUTING_PRIMARY", None)
        if self._orig_t:
            os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = self._orig_t
        else:
            os.environ.pop("OPENAI_ROUTING_CONFIDENCE_THRESHOLD", None)

    def test_high_confidence_uses_llm(self):
        client = MockOpenAIClient(
            response_json={
                "intent": "refund_request",
                "department": "Returns Admin",
                "confidence": 0.95,
            }
        )
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "refund please"},
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(artifact.primary_source, "llm")
        self.assertIn("mw-llm-routed", routing.tags)

    def test_low_confidence_uses_deterministic(self):
        client = MockOpenAIClient(
            response_json={
                "intent": "refund_request",
                "department": "Returns Admin",
                "confidence": 0.5,
            }
        )
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "Where is my order?"},
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(artifact.primary_source, "deterministic")


class ForcePrimaryTests(unittest.TestCase):
    def setUp(self):
        self._orig_primary = os.environ.get("OPENAI_ROUTING_PRIMARY")
        self._orig_threshold = os.environ.get("OPENAI_ROUTING_CONFIDENCE_THRESHOLD")
        os.environ["OPENAI_ROUTING_PRIMARY"] = "false"
        os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = "0.9"

    def tearDown(self):
        if self._orig_primary is not None:
            os.environ["OPENAI_ROUTING_PRIMARY"] = self._orig_primary
        else:
            os.environ.pop("OPENAI_ROUTING_PRIMARY", None)
        if self._orig_threshold is not None:
            os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = self._orig_threshold
        else:
            os.environ.pop("OPENAI_ROUTING_CONFIDENCE_THRESHOLD", None)

    def test_force_primary_respects_threshold(self):
        client = MockOpenAIClient(
            response_json={
                "intent": "refund_request",
                "department": "Returns Admin",
                "confidence": 0.5,
            }
        )
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "refund please"},
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
            force_primary=True,
        )
        self.assertEqual(artifact.primary_source, "deterministic")
        self.assertNotIn("mw-llm-routed", routing.tags)

    def test_force_primary_uses_llm_when_confident(self):
        client = MockOpenAIClient(
            response_json={
                "intent": "refund_request",
                "department": "Returns Admin",
                "confidence": 0.95,
            }
        )
        routing, artifact = compute_dual_routing(
            payload={"customer_message": "refund please"},
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
            force_primary=True,
        )
        self.assertEqual(artifact.primary_source, "llm")
        self.assertIn("mw-llm-routed", routing.tags)


class ResponseIdReasonTests(unittest.TestCase):
    class _RawlessClient:
        def __init__(self):
            self.calls = 0

        def chat_completion(self, request, *, safe_mode, automation_enabled):
            self.calls += 1
            return ChatCompletionResponse(
                model=request.model,
                message=json.dumps(
                    {
                        "intent": "order_status_tracking",
                        "department": "Email Support Team",
                        "confidence": 0.9,
                    }
                ),
                status_code=200,
                url="test",
                raw={},
                dry_run=False,
            )

    def test_response_id_reason_when_raw_empty(self):
        client = self._RawlessClient()
        suggestion = suggest_llm_routing(
            customer_message="test",
            conversation_id="c",
            event_id="e",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        self.assertEqual(client.calls, 1)
        self.assertEqual(
            suggestion.response_id_unavailable_reason, "response_id_missing"
        )


class SuggestionTests(unittest.TestCase):
    def test_is_valid_with_valid_data(self):
        s = LLMRoutingSuggestion(
            intent="order_status_tracking",
            department="Email Support Team",
            confidence=0.9,
        )
        self.assertTrue(s.is_valid())

    def test_is_valid_with_invalid_intent(self):
        s = LLMRoutingSuggestion(
            intent="not_real", department="Email Support Team", confidence=0.9
        )
        self.assertFalse(s.is_valid())

    def test_passes_threshold(self):
        s = LLMRoutingSuggestion(
            intent="order_status_tracking",
            department="Email Support Team",
            confidence=0.9,
        )
        self.assertTrue(s.passes_threshold(0.85))
        self.assertFalse(s.passes_threshold(0.95))


class ThresholdTests(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.get("OPENAI_ROUTING_CONFIDENCE_THRESHOLD")
        self._orig_min = os.environ.get("OPENAI_ROUTING_MIN_CONFIDENCE")

    def tearDown(self):
        if self._orig:
            os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = self._orig
        else:
            os.environ.pop("OPENAI_ROUTING_CONFIDENCE_THRESHOLD", None)
        if self._orig_min:
            os.environ["OPENAI_ROUTING_MIN_CONFIDENCE"] = self._orig_min
        else:
            os.environ.pop("OPENAI_ROUTING_MIN_CONFIDENCE", None)

    def test_default_threshold(self):
        os.environ.pop("OPENAI_ROUTING_CONFIDENCE_THRESHOLD", None)
        os.environ.pop("OPENAI_ROUTING_MIN_CONFIDENCE", None)
        self.assertEqual(get_confidence_threshold(), DEFAULT_CONFIDENCE_THRESHOLD)

    def test_custom_threshold(self):
        os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = "0.7"
        self.assertEqual(get_confidence_threshold(), 0.7)

    def test_min_confidence_overrides_legacy(self):
        os.environ["OPENAI_ROUTING_MIN_CONFIDENCE"] = "0.42"
        os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = "0.9"
        self.assertEqual(get_confidence_threshold(), 0.42)

    def test_min_confidence_invalid_falls_back(self):
        os.environ["OPENAI_ROUTING_MIN_CONFIDENCE"] = "not-a-float"
        os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = "0.6"
        self.assertEqual(get_confidence_threshold(), DEFAULT_CONFIDENCE_THRESHOLD)

    def test_min_confidence_negative_falls_back(self):
        os.environ["OPENAI_ROUTING_MIN_CONFIDENCE"] = "-0.5"
        self.assertEqual(get_confidence_threshold(), DEFAULT_CONFIDENCE_THRESHOLD)

    def test_min_confidence_above_one_falls_back(self):
        os.environ["OPENAI_ROUTING_MIN_CONFIDENCE"] = "1.5"
        self.assertEqual(get_confidence_threshold(), DEFAULT_CONFIDENCE_THRESHOLD)

    def test_min_confidence_empty_string_falls_back(self):
        os.environ["OPENAI_ROUTING_MIN_CONFIDENCE"] = ""
        self.assertEqual(get_confidence_threshold(), DEFAULT_CONFIDENCE_THRESHOLD)

    def test_legacy_confidence_whitespace_falls_back(self):
        os.environ.pop("OPENAI_ROUTING_MIN_CONFIDENCE", None)
        os.environ["OPENAI_ROUTING_CONFIDENCE_THRESHOLD"] = "   "
        self.assertEqual(get_confidence_threshold(), DEFAULT_CONFIDENCE_THRESHOLD)


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(GatingTests))
    suite.addTests(loader.loadTestsFromTestCase(ArtifactTests))
    suite.addTests(loader.loadTestsFromTestCase(PrimaryFlagTests))
    suite.addTests(loader.loadTestsFromTestCase(PrimaryFlagOnTests))
    suite.addTests(loader.loadTestsFromTestCase(ForcePrimaryTests))
    suite.addTests(loader.loadTestsFromTestCase(ResponseIdReasonTests))
    suite.addTests(loader.loadTestsFromTestCase(SuggestionTests))
    suite.addTests(loader.loadTestsFromTestCase(ThresholdTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
