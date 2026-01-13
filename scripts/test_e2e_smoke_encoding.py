#!/usr/bin/env python3
"""
test_e2e_smoke_encoding.py

Unit tests for E2E smoke script URL encoding and scenario payload handling.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Import after path setup
sys.path.insert(0, str(ROOT / "scripts"))
from dev_e2e_smoke import _order_status_scenario_payload  # noqa: E402


class ScenarioPayloadTests(unittest.TestCase):
    def test_order_status_scenario_includes_required_fields(self) -> None:
        """Ensure order_status scenario payload includes all required fields."""
        payload = _order_status_scenario_payload("TEST_RUN", conversation_id="test-conv-123")

        # Required fields for offline order summary
        self.assertEqual(payload["scenario"], "order_status")
        self.assertEqual(payload["intent"], "order_status_tracking")
        self.assertIn("customer_message", payload)
        self.assertIn("tracking_number", payload)
        self.assertIn("carrier", payload)
        self.assertIn("shipping_method", payload)
        self.assertIn("order_id", payload)
        self.assertIn("status", payload)
        self.assertIn("fulfillment_status", payload)

    def test_order_status_scenario_is_deterministic(self) -> None:
        """Scenario payload should be deterministic for same run_id."""
        payload1 = _order_status_scenario_payload("RUN_A", conversation_id="conv-1")
        payload2 = _order_status_scenario_payload("RUN_A", conversation_id="conv-1")

        self.assertEqual(payload1["tracking_number"], payload2["tracking_number"])
        self.assertEqual(payload1["order_id"], payload2["order_id"])

    def test_order_status_scenario_no_pii(self) -> None:
        """Scenario payload must not contain PII patterns."""
        payload = _order_status_scenario_payload("TEST", conversation_id="test-123")

        import json
        serialized = json.dumps(payload)
        self.assertNotIn("@", serialized)
        self.assertNotIn("%40", serialized)
        self.assertNotIn("mail.", serialized)


class URLEncodingTests(unittest.TestCase):
    def test_middleware_encodes_email_based_conversation_id(self) -> None:
        """Middleware must URL-encode email-based conversation IDs for write paths."""
        from richpanel_middleware.automation.pipeline import execute_routing_tags
        from richpanel_middleware.ingest.envelope import EventEnvelope
        from richpanel_middleware.automation.pipeline import ActionPlan, RoutingDecision

        # Create envelope with email-based conversation ID (contains @ and <>)
        email_id = "<test@mail.example.com>"
        envelope = EventEnvelope(
            event_id="evt:test",
            received_at="2026-01-13T00:00:00Z",
            group_id="test-group",
            dedupe_id="test-dedupe",
            payload={"customer_message": "test"},
            source="test",
            conversation_id=email_id,
        )

        routing = RoutingDecision(
            category="order_status",
            tags=["mw-routing-applied"],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        plan = ActionPlan(
            event_id="evt:test",
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[],
            reasons=[],
            routing=routing,
            routing_artifact=None,
        )

        # Mock executor to record the path used
        mock_executor = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.dry_run = False
        mock_executor.execute.return_value = mock_response

        # Execute with mocked executor
        result = execute_routing_tags(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=mock_executor,
        )

        # Assert executor.execute was called with URL-encoded path
        self.assertTrue(mock_executor.execute.called)
        call_args = mock_executor.execute.call_args
        path_arg = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("path")

        # Path should be URL-encoded (no raw <, >, @)
        self.assertNotIn("<", path_arg)
        self.assertNotIn(">", path_arg)
        self.assertNotIn("@", path_arg)
        # Should contain percent-encoded equivalents
        self.assertIn("%", path_arg)

    def test_middleware_encodes_plus_sign_in_conversation_id(self) -> None:
        """Middleware must URL-encode + signs in conversation IDs."""
        from richpanel_middleware.automation.pipeline import execute_routing_tags
        from richpanel_middleware.ingest.envelope import EventEnvelope
        from richpanel_middleware.automation.pipeline import ActionPlan, RoutingDecision

        # Create envelope with + in conversation ID
        plus_id = "test+id+with+plus@mail.com"
        envelope = EventEnvelope(
            event_id="evt:test",
            received_at="2026-01-13T00:00:00Z",
            group_id="test-group",
            dedupe_id="test-dedupe",
            payload={"customer_message": "test"},
            source="test",
            conversation_id=plus_id,
        )

        routing = RoutingDecision(
            category="general",
            tags=["test"],
            reason="test",
            department="Email Support Team",
            intent="unknown",
        )
        plan = ActionPlan(
            event_id="evt:test",
            mode="route_only",
            safe_mode=False,
            automation_enabled=True,
            actions=[],
            reasons=[],
            routing=routing,
            routing_artifact=None,
        )

        mock_executor = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.dry_run = False
        mock_executor.execute.return_value = mock_response

        result = execute_routing_tags(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=mock_executor,
        )

        call_args = mock_executor.execute.call_args
        path_arg = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("path")

        # + should be encoded as %2B
        self.assertNotIn("+", path_arg)
        self.assertIn("%2B", path_arg)


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ScenarioPayloadTests))
    suite.addTests(loader.loadTestsFromTestCase(URLEncodingTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
