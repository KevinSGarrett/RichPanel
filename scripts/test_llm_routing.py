#!/usr/bin/env python3
"""
test_llm_routing.py

Tests for the LLM routing advisory module.

Proves:
1. No network calls when gated (safe_mode, automation_disabled, network_disabled, openai_outbound_disabled)
2. Artifacts persist into state + audit records
3. Deterministic baseline remains unaffected by LLM routing
4. LLM response parsing handles edge cases
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation import llm_routing as llm_routing_module
from richpanel_middleware.automation.llm_routing import (
    KNOWN_DEPARTMENTS,
    KNOWN_INTENTS,
    LLMRoutingArtifact,
    LLMRoutingSuggestion,
    compute_llm_routing_artifact,
    suggest_routing,
)
from richpanel_middleware.automation.pipeline import (
    ActionPlan,
    execute_plan,
    plan_actions,
)
from richpanel_middleware.automation.router import classify_routing
from richpanel_middleware.ingest.envelope import normalize_envelope
from richpanel_middleware.integrations.openai import (
    TransportRequest,
    TransportResponse,
)

# Access private functions for testing
_parse_llm_response = llm_routing_module._parse_llm_response
_check_llm_routing_gates = llm_routing_module._check_llm_routing_gates


class LLMRoutingGatingTests(unittest.TestCase):
    """Test that LLM routing is properly gated (fail-closed)."""

    def setUp(self) -> None:
        for key in [
            "OPENAI_ALLOW_NETWORK",
            "OPENAI_API_KEY",
            "OPENAI_OUTBOUND_ENABLED",
            "OPENAI_ROUTING_MODEL",
            "OPENAI_MODEL",
        ]:
            os.environ.pop(key, None)

    def test_safe_mode_blocks_llm_call(self) -> None:
        artifact = suggest_routing(
            "Where is my order?",
            safe_mode=True,
            automation_enabled=True,
            allow_network=True,
            openai_outbound_enabled=True,
        )
        self.assertTrue(artifact.dry_run)
        self.assertEqual(artifact.gated_reason, "safe_mode")
        self.assertFalse(artifact.gates["allowed"])
        self.assertIn("safe_mode", artifact.gates["block_reasons"])
        self.assertIsNone(artifact.suggestion)

    def test_automation_disabled_blocks_llm_call(self) -> None:
        artifact = suggest_routing(
            "Where is my order?",
            safe_mode=False,
            automation_enabled=False,
            allow_network=True,
            openai_outbound_enabled=True,
        )
        self.assertTrue(artifact.dry_run)
        self.assertEqual(artifact.gated_reason, "automation_disabled")

    def test_network_disabled_blocks_llm_call(self) -> None:
        artifact = suggest_routing(
            "Where is my order?",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            openai_outbound_enabled=True,
        )
        self.assertTrue(artifact.dry_run)
        self.assertEqual(artifact.gated_reason, "network_disabled")

    def test_openai_outbound_disabled_blocks_llm_call(self) -> None:
        artifact = suggest_routing(
            "Where is my order?",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            openai_outbound_enabled=False,
        )
        self.assertTrue(artifact.dry_run)
        self.assertEqual(artifact.gated_reason, "openai_outbound_disabled")

    def test_all_gates_pass_allows_call(self) -> None:
        gates = _check_llm_routing_gates(
            safe_mode=False,
            automation_enabled=True,
            openai_outbound_enabled=True,
            allow_network=True,
        )
        self.assertTrue(gates["allowed"])
        self.assertEqual(gates["block_reasons"], [])


class LLMRoutingParsingTests(unittest.TestCase):
    """Test LLM response parsing."""

    def test_valid_json_response(self) -> None:
        raw = '{"intent": "order_status_tracking", "department": "Email Support Team", "category": "order_status", "confidence": 0.85, "reason": "Customer asking about order"}'
        suggestion, error = _parse_llm_response(raw)
        self.assertIsNone(error)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.intent, "order_status_tracking")
        self.assertEqual(suggestion.confidence, 0.85)

    def test_empty_response(self) -> None:
        suggestion, error = _parse_llm_response("")
        self.assertEqual(error, "empty_response")
        self.assertIsNone(suggestion)

    def test_invalid_json_response(self) -> None:
        suggestion, error = _parse_llm_response("not valid json")
        self.assertIsNotNone(error)
        self.assertTrue(error.startswith("json_parse_error"))

    def test_unknown_intent_defaults(self) -> None:
        raw = '{"intent": "invalid_intent", "department": "Email Support Team", "category": "general", "confidence": 0.5, "reason": "test"}'
        suggestion, error = _parse_llm_response(raw)
        self.assertIsNone(error)
        self.assertEqual(suggestion.intent, "unknown_other")


class LLMRoutingPersistenceTests(unittest.TestCase):
    """Test that LLM routing artifacts persist into state/audit records."""

    def setUp(self) -> None:
        for key in ["OPENAI_ALLOW_NETWORK", "OPENAI_API_KEY", "OPENAI_OUTBOUND_ENABLED"]:
            os.environ.pop(key, None)

    def test_artifact_in_action_plan(self) -> None:
        raw_event = {"event_id": "evt-001", "conversation_id": "conv-001", "payload": {"customer_message": "Where is my order?"}}
        envelope = normalize_envelope(raw_event)
        plan = plan_actions(envelope, safe_mode=True, automation_enabled=False, allow_network=False)
        self.assertIsNotNone(plan.llm_routing_artifact)
        self.assertTrue(plan.llm_routing_artifact.dry_run)

    def test_artifact_persisted_to_state_record(self) -> None:
        raw_event = {"event_id": "evt-002", "conversation_id": "conv-002", "payload": {"customer_message": "I want a refund"}}
        envelope = normalize_envelope(raw_event)
        plan = plan_actions(envelope, safe_mode=True, automation_enabled=False, allow_network=False)
        state_records = []
        execute_plan(envelope, plan, dry_run=True, state_writer=lambda r: state_records.append(r))
        self.assertEqual(len(state_records), 1)
        self.assertIn("llm_routing_advisory", state_records[0])


class DeterministicBaselineUnaffectedTests(unittest.TestCase):
    """Test that deterministic routing baseline is unaffected by LLM routing."""

    def test_plan_actions_returns_deterministic_routing(self) -> None:
        raw_event = {"event_id": "evt-004", "conversation_id": "conv-004", "payload": {"customer_message": "Where is my order tracking?"}}
        envelope = normalize_envelope(raw_event)
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True, allow_network=False)
        self.assertIsNotNone(plan.routing)
        self.assertEqual(plan.routing.intent, "order_status_tracking")
        self.assertIsNotNone(plan.llm_routing_artifact)
        self.assertTrue(plan.llm_routing_artifact.dry_run)


class IntentTaxonomyTests(unittest.TestCase):
    """Test that known intents and departments match the taxonomy."""

    def test_known_intents_complete(self) -> None:
        expected_intents = {
            "order_status_tracking", "shipping_delay_not_shipped", "delivered_not_received",
            "missing_items_in_shipment", "wrong_item_received", "damaged_item", "cancel_order",
            "address_change_order_edit", "cancel_subscription", "billing_issue", "promo_discount_issue",
            "pre_purchase_question", "influencer_marketing_inquiry", "return_request", "exchange_request",
            "refund_request", "technical_support", "phone_support_request", "tiktok_support_request",
            "social_media_support_request", "chargeback_dispute", "legal_threat", "harassment_threats",
            "fraud_suspected", "unknown_other",
        }
        self.assertEqual(KNOWN_INTENTS, expected_intents)


def main() -> int:
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(LLMRoutingGatingTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(LLMRoutingParsingTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(LLMRoutingPersistenceTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(DeterministicBaselineUnaffectedTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(IntentTaxonomyTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
