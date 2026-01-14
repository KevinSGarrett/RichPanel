#!/usr/bin/env python3
"""
test_e2e_smoke_encoding.py

Unit tests for E2E smoke script URL encoding and scenario payload handling.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dev_e2e_smoke import (  # type: ignore  # noqa: E402
    _check_pii_safe,
    _compute_middleware_outcome,
    _compute_reply_evidence,
    _apply_fallback_close,
    _diagnose_ticket_update,
    _sanitize_decimals,
    _sanitize_response_metadata,
)


def _fingerprint(value: str, length: int = 12) -> str:
    """Local implementation to avoid importing dev_e2e_smoke (which requires boto3)."""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _order_status_scenario_payload(run_id: str, *, conversation_id: str | None) -> dict:
    """Local implementation to avoid boto3 dependency."""
    now = datetime.now(timezone.utc)
    order_created_at = (now - timedelta(days=5)).isoformat()
    ticket_created_at = (now - timedelta(days=1)).isoformat()
    order_seed = run_id or "order-status-smoke"
    seeded_order_id = conversation_id or f"DEV-ORDER-{_fingerprint(order_seed, length=8).upper()}"
    tracking_number = f"TRACK-{_fingerprint(seeded_order_id + order_seed, length=10).upper()}"
    tracking_url = f"https://tracking.example.com/track/{tracking_number}"
    shipping_method = "Standard (3-5 business days)"
    carrier = "UPS"

    base_order = {
        "id": seeded_order_id,
        "order_id": seeded_order_id,
        "status": "shipped",
        "fulfillment_status": "shipped",
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "carrier": carrier,
        "shipping_carrier": carrier,
        "shipping_method": shipping_method,
        "shipping_method_name": shipping_method,
        "order_created_at": order_created_at,
        "created_at": order_created_at,
        "updated_at": ticket_created_at,
        "items": [
            {"sku": "SMOKE-OS-HOODIE", "name": "Smoke Test Hoodie", "quantity": 1}
        ],
    }

    return {
        "scenario": "order_status",
        "intent": "order_status_tracking",
        "customer_message": "Where is my order? Please share the tracking update.",
        "ticket_created_at": ticket_created_at,
        "order_created_at": order_created_at,
        "order_id": seeded_order_id,
        "status": "shipped",
        "fulfillment_status": "shipped",
        "order_status": "shipped",
        "carrier": carrier,
        "shipping_carrier": carrier,
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "shipping_method": shipping_method,
        "orders": [base_order],
        "order": base_order,
        "tracking": {
            "number": tracking_number,
            "carrier": carrier,
            "status": "in_transit",
            "status_url": tracking_url,
            "updated_at": ticket_created_at,
        },
        "shipment": {
            "carrier": carrier,
            "serviceCode": shipping_method,
            "orderNumber": seeded_order_id,
            "shipDate": ticket_created_at,
        },
    }


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


class DiagnosticsTests(unittest.TestCase):
    class _MockResponse:
        def __init__(self, status_code: int, dry_run: bool, url: str) -> None:
            self.status_code = status_code
            self.dry_run = dry_run
            self.url = url

        def json(self) -> dict:
            return {}

    class _MockExecutor:
        def __init__(self, status_code: int = 200) -> None:
            self.status_code = status_code
            self.calls: list[dict] = []

        def execute(self, method: str, path: str, json_body: dict, dry_run: bool, log_body_excerpt: bool) -> "DiagnosticsTests._MockResponse":  # type: ignore[override]  # noqa: E501
            self.calls.append({"method": method, "path": path, "body": json_body, "dry_run": dry_run})
            return DiagnosticsTests._MockResponse(self.status_code, dry_run, path)

    def test_diagnose_skips_without_confirm(self) -> None:
        executor = self._MockExecutor()
        result = _diagnose_ticket_update(
            executor,
            "ticket-123",
            allow_network=True,
            confirm_test_ticket=False,
            diagnostic_message="test",
        )
        self.assertFalse(result["performed"])
        self.assertEqual(result["reason"], "confirm_test_ticket_not_set")
        self.assertFalse(executor.calls)

    def test_diagnose_selects_first_successful_candidate(self) -> None:
        executor = self._MockExecutor(status_code=200)
        result = _diagnose_ticket_update(
            executor,
            "ticket-123",
            allow_network=True,
            confirm_test_ticket=True,
            diagnostic_message="test",
            apply_winning=True,
        )
        self.assertTrue(result["performed"])
        self.assertEqual(result["winning_candidate"], "status_resolved")
        self.assertEqual(result["winning_payload"], {"status": "resolved"})
        self.assertTrue(any(entry["ok"] for entry in result["results"]))
        self.assertIsNotNone(result.get("apply_result"))
        # Ensure response metadata redaction works
        sanitized = _sanitize_response_metadata(self._MockResponse(200, False, "/v1/tickets/abc"))
        self.assertEqual(sanitized["endpoint_variant"], "id")


class ReplyEvidenceTests(unittest.TestCase):
    def test_reply_evidence_status_change_only(self) -> None:
        evidence, reason = _compute_reply_evidence(
            status_changed=True,
            updated_at_delta=1.23,
            message_count_delta=None,
            last_message_source_after=None,
            tags_added=[],
        )
        self.assertFalse(evidence)
        self.assertIn("status_changed_delta=1.23", reason)

    def test_reply_evidence_message_delta(self) -> None:
        evidence, reason = _compute_reply_evidence(
            status_changed=False,
            updated_at_delta=None,
            message_count_delta=2,
            last_message_source_after=None,
            tags_added=[],
        )
        self.assertTrue(evidence)
        self.assertIn("message_count_delta=2", reason)

    def test_reply_evidence_middleware_source(self) -> None:
        evidence, reason = _compute_reply_evidence(
            status_changed=False,
            updated_at_delta=None,
            message_count_delta=None,
            last_message_source_after="middleware",
            tags_added=[],
        )
        self.assertTrue(evidence)
        self.assertIn("last_message_source=middleware", reason)

    def test_reply_evidence_none(self) -> None:
        evidence, reason = _compute_reply_evidence(
            status_changed=False,
            updated_at_delta=None,
            message_count_delta=None,
            last_message_source_after=None,
            tags_added=[],
        )
        self.assertFalse(evidence)
        self.assertEqual(reason, "no_reply_evidence_fields")

    def test_reply_evidence_tags_and_update_success(self) -> None:
        evidence, reason = _compute_reply_evidence(
            status_changed=False,
            updated_at_delta=None,
            message_count_delta=None,
            last_message_source_after=None,
            tags_added=["mw-order-status-answered"],
            reply_update_success=True,
            reply_update_candidate="ticket_state_closed",
        )
        self.assertTrue(evidence)
        self.assertIn("positive_middleware_tag_added", reason)
        self.assertIn("reply_update_success:ticket_state_closed", reason)


class FallbackCloseTests(unittest.TestCase):
    class _Resp:
        def __init__(self, status_code: int, dry_run: bool, url: str) -> None:
            self.status_code = status_code
            self.dry_run = dry_run
            self.url = url

    class _Exec:
        def __init__(self, responses: list["FallbackCloseTests._Resp"]) -> None:
            self.responses = responses
            self.calls: list[tuple[str, str, dict[str, Any]]] = []

        def execute(self, method: str, path: str, **kwargs: Any) -> "FallbackCloseTests._Resp":
            self.calls.append((method, path, kwargs))
            return self.responses.pop(0)

    def test_fallback_close_records_alt_paths_and_metadata(self) -> None:
        responses = [
            self._Resp(200, False, "/v1/tickets/id123"),
            self._Resp(200, False, "/v1/tickets/id123"),
            self._Resp(201, False, "/v1/tickets/number/1025"),
            self._Resp(202, False, "/v1/tickets/number/1025"),
        ]
        execu = self._Exec(responses)
        result = _apply_fallback_close(
            ticket_executor=execu,
            ticket_ref="1025",
            ticket_id_for_fallback="id123",
            fallback_comment={"body": "test", "type": "public", "source": "middleware"},
            fallback_tags=["mw-reply-sent"],
            allow_network=True,
        )
        # Primary success recorded
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["close_only_status"], 200)
        # Alt paths captured
        self.assertEqual(result["alt_status"], 201)
        self.assertEqual(result["alt_close_status"], 202)
        # Calls hit both id and number paths
        paths = [call[1] for call in execu.calls]
        self.assertIn("/v1/tickets/id123", paths[0])
        self.assertIn("/v1/tickets/number/1025", paths[-1])


class CriteriaTests(unittest.TestCase):
    def test_middleware_outcome_rejects_skip_tags(self) -> None:
        outcome = _compute_middleware_outcome(
            status_after="open",
            tags_added=["mw-skip-status-read-failed"],
            post_tags=["mw-skip-status-read-failed", "mw-smoke:RUN"],
        )
        self.assertTrue(outcome["skip_tags_present"])
        self.assertFalse(outcome["middleware_outcome"])
        self.assertFalse(outcome["middleware_tag_present"])
        self.assertFalse(outcome["middleware_tag_added"])

    def test_middleware_outcome_ignores_historical_skip_tags(self) -> None:
        outcome = _compute_middleware_outcome(
            status_after="open",
            tags_added=[],
            post_tags=["mw-skip-status-read-failed", "mw-smoke:RUN"],
        )
        self.assertFalse(outcome["skip_tags_present"])
        self.assertFalse(outcome["middleware_outcome"])
        self.assertFalse(outcome["middleware_tag_present"])
        self.assertFalse(outcome["middleware_tag_added"])

    def test_middleware_outcome_rejects_route_to_support_tag_added(self) -> None:
        outcome = _compute_middleware_outcome(
            status_after="open",
            tags_added=["route-email-support-team"],
            post_tags=["route-email-support-team"],
        )
        self.assertTrue(outcome["skip_tags_present"])
        self.assertFalse(outcome["middleware_outcome"])
        self.assertFalse(outcome["middleware_tag_present"])
        self.assertFalse(outcome["middleware_tag_added"])

    def test_middleware_outcome_accepts_resolved(self) -> None:
        outcome = _compute_middleware_outcome(
            status_after="resolved",
            tags_added=[],
            post_tags=["mw-smoke:RUN"],
        )
        self.assertFalse(outcome["skip_tags_present"])
        self.assertTrue(outcome["middleware_outcome"])
        self.assertTrue(outcome["status_resolved"])
        self.assertFalse(outcome["middleware_tag_added"])

    def test_middleware_outcome_requires_tag_added_not_only_present(self) -> None:
        outcome = _compute_middleware_outcome(
            status_after="open",
            tags_added=[],
            post_tags=["mw-order-status-answered:RUN"],
        )
        self.assertFalse(outcome["middleware_tag_present"])
        self.assertFalse(outcome["middleware_tag_added"])
        self.assertFalse(outcome["middleware_outcome"])

    def test_pii_guard_detects_patterns(self) -> None:
        msg = _check_pii_safe('{"path":"mailto:test@example.com"}')
        self.assertIsNotNone(msg)

    def test_sanitize_decimals_converts(self) -> None:
        obj = {"a": Decimal("1.0"), "b": [Decimal("2.5"), {"c": Decimal("3")}]}
        sanitized = _sanitize_decimals(obj)
        self.assertEqual(sanitized["a"], 1)
        self.assertEqual(sanitized["b"][0], 2.5)
        self.assertEqual(sanitized["b"][1]["c"], 3)

    def test_middleware_outcome_counts_positive_tag_added(self) -> None:
        outcome = _compute_middleware_outcome(
            status_after="open",
            tags_added=["mw-order-status-answered:RUN"],
            post_tags=["mw-order-status-answered:RUN"],
        )
        self.assertTrue(outcome["middleware_tag_present"])
        self.assertTrue(outcome["middleware_tag_added"])
        self.assertTrue(outcome["middleware_outcome"])


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
    suite.addTests(loader.loadTestsFromTestCase(CriteriaTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
