from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import cast
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Ensure required env vars exist for imports that expect them.
os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "local-idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/local/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/local/automation_enabled")
os.environ.setdefault("CONVERSATION_STATE_TABLE_NAME", "local-conversation-state")
os.environ.setdefault("AUDIT_TRAIL_TABLE_NAME", "local-audit-trail")
os.environ.setdefault("CONVERSATION_STATE_TTL_SECONDS", "3600")
os.environ.setdefault("AUDIT_TRAIL_TTL_SECONDS", "3600")

from richpanel_middleware.automation.pipeline import (  # noqa: E402
    _missing_order_context,
    _tracking_signal_present,
    plan_actions,
)
from richpanel_middleware.automation.router import RoutingDecision  # noqa: E402
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402


class OrderStatusContextGateTests(unittest.TestCase):
    def test_missing_order_id_no_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-missing-order-id",
                "created_at": "2025-01-01T00:00:00Z",
                "tracking_number": "1Z000",
                "carrier": "UPS",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertNotIn("order_status_draft_reply", action_types)
        self.assertIn("order_context_missing", plan.reasons)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertIn("route-email-support-team", routing.tags)
        self.assertIn("mw-order-lookup-failed", routing.tags)
        self.assertIn("mw-order-status-suppressed", routing.tags)
        self.assertIn("mw-order-lookup-missing:order_id", routing.tags)

    def test_missing_created_at_no_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-missing-created-at",
                "order_id": "ord-missing-created",
                "tracking_number": "1Z333",
                "carrier": "UPS",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertNotIn("order_status_draft_reply", action_types)
        self.assertIn("order_context_missing", plan.reasons)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertIn("route-email-support-team", routing.tags)
        self.assertIn("mw-order-lookup-failed", routing.tags)
        self.assertIn("mw-order-status-suppressed", routing.tags)
        self.assertIn("mw-order-lookup-missing:created_at", routing.tags)

    def test_missing_tracking_and_shipping_method_no_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-missing-tracking",
                "order_id": "ord-missing-tracking",
                "created_at": "2025-01-01T00:00:00Z",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertNotIn("order_status_draft_reply", action_types)
        self.assertIn("order_context_missing", plan.reasons)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertIn("route-email-support-team", routing.tags)
        self.assertIn("mw-order-lookup-failed", routing.tags)
        self.assertIn("mw-order-status-suppressed", routing.tags)
        self.assertIn(
            "mw-order-lookup-missing:tracking_or_shipping_method", routing.tags
        )

    def test_missing_shipping_method_bucket_no_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-missing-bucket",
                "order_id": "ord-missing-bucket",
                "created_at": "2025-01-01T00:00:00Z",
                "shipping_method": "quantum courier",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertNotIn("order_status_draft_reply", action_types)
        self.assertIn("order_context_missing", plan.reasons)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertIn("route-email-support-team", routing.tags)
        self.assertIn("mw-order-lookup-failed", routing.tags)
        self.assertIn("mw-order-status-suppressed", routing.tags)
        self.assertIn("mw-order-lookup-missing:shipping_method_bucket", routing.tags)

    def test_none_order_summary_no_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-none-summary",
                "message": "Where is my order?",
            }
        )
        with mock.patch(
            "richpanel_middleware.automation.pipeline.lookup_order_summary",
            return_value=None,
        ):
            plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertNotIn("order_status_draft_reply", action_types)
        self.assertIn("order_context_missing", plan.reasons)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertIn("mw-order-lookup-failed", routing.tags)
        self.assertIn("mw-order-status-suppressed", routing.tags)
        self.assertIn("mw-order-lookup-missing:order_id", routing.tags)

    def test_empty_string_order_id_no_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-empty-order-id",
                "created_at": "2025-01-01T00:00:00Z",
                "tracking_number": "1ZEMPTY",
                "carrier": "UPS",
                "message": "Where is my order?",
            }
        )
        order_summary = {
            "order_id": "",
            "created_at": "2025-01-01T00:00:00Z",
            "tracking_number": "1ZEMPTY",
            "carrier": "UPS",
        }
        with mock.patch(
            "richpanel_middleware.automation.pipeline.lookup_order_summary",
            return_value=order_summary,
        ):
            plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertNotIn("order_status_draft_reply", action_types)
        self.assertIn("order_context_missing", plan.reasons)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertIn("mw-order-lookup-missing:order_id", routing.tags)

    def test_multiple_missing_fields_logs_all(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-missing-fields",
                "message": "Where is my order?",
            }
        )
        missing_fields = _missing_order_context(None, envelope, envelope.payload or {})
        self.assertEqual(
            {"order_id", "created_at", "tracking_or_shipping_method"},
            set(missing_fields),
        )

    def test_tracking_signal_with_empty_strings(self) -> None:
        summary = {
            "tracking_url": "",
            "tracking_link": "",
            "status_url": None,
            "tracking_number": "",
            "carrier": "",
        }
        self.assertFalse(_tracking_signal_present(summary))

    def test_full_context_proceeds_normally(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-full",
                "order_id": "ord-full",
                "created_at": "2025-01-01T00:00:00Z",
                "tracking_number": "1Z222",
                "carrier": "UPS",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        order_actions = [
            action
            for action in plan.actions
            if action["type"] == "order_status_draft_reply"
        ]
        self.assertEqual(len(order_actions), 1)
        draft_reply = order_actions[0]["parameters"].get("draft_reply", {})
        self.assertIn("body", draft_reply)
        self.assertIn("Tracking number", draft_reply["body"])

    def test_full_context_with_camelcase_tracking_url(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-camelcase-tracking",
                "message": "Where is my order?",
            }
        )
        order_summary = {
            "order_id": "ORDER-123",
            "created_at": "2025-01-01T00:00:00Z",
            "trackingUrl": "https://tracking.example.com/12345",
        }
        with mock.patch(
            "richpanel_middleware.automation.pipeline.lookup_order_summary",
            return_value=order_summary,
        ):
            plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        action_types = [action["type"] for action in plan.actions]
        self.assertIn("order_status_draft_reply", action_types)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertNotIn("mw-order-lookup-failed", routing.tags)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
