from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    execute_plan,
    normalize_event,
    plan_actions,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from lambda_handlers.worker import handler as worker  # noqa: E402


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        # Reset worker caches so each test is deterministic and offline-safe.
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update({"safe_mode": True, "automation_enabled": False, "expires_at": 0.0})
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None

    def test_normalize_event_populates_defaults(self) -> None:
        envelope = normalize_event({"payload": {"ticket_id": "t-123", "message_id": "m-1"}})

        self.assertEqual(envelope.conversation_id, "t-123")
        self.assertEqual(envelope.dedupe_id, "m-1")
        self.assertTrue(envelope.event_id.startswith("evt:"))
        self.assertTrue(envelope.received_at)

    def test_plan_respects_safe_mode(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-456"})
        plan = plan_actions(envelope, safe_mode=True, automation_enabled=True)

        self.assertEqual(plan.mode, "route_only")
        self.assertIn("safe_mode", plan.reasons)
        self.assertEqual(plan.actions[0]["type"], "route_only")

    def test_plan_allows_automation_candidate(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-789", "order_id": "ord-789"})
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        self.assertEqual(plan.mode, "automation_candidate")
        self.assertEqual(plan.actions[0]["type"], "analyze")
        order_actions = [action for action in plan.actions if action["type"] == "order_status_draft_reply"]
        self.assertEqual(len(order_actions), 1)
        order_action = order_actions[0]
        self.assertFalse(order_action["enabled"])
        self.assertTrue(order_action["dry_run"])
        self.assertIn("order_summary", order_action["parameters"])
        self.assertIn("prompt_fingerprint", order_action["parameters"])
        self.assertEqual(order_action["parameters"]["order_summary"]["order_id"], "ord-789")

    def test_execute_plan_dry_run_records(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-000"})
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=False)

        captured_state = []
        captured_audit = []

        def state_writer(record):
            captured_state.append(record)

        def audit_writer(record):
            captured_audit.append(record)

        result = execute_plan(
            envelope,
            plan,
            dry_run=True,
            state_writer=state_writer,
            audit_writer=audit_writer,
        )

        self.assertTrue(result.dry_run)
        self.assertEqual(result.state_record["event_id"], envelope.event_id)
        self.assertEqual(result.state_record["mode"], plan.mode)
        self.assertEqual(result.audit_record["mode"], plan.mode)
        self.assertEqual(len(captured_state), 1)
        self.assertEqual(len(captured_audit), 1)

    def test_build_event_envelope_truncates_and_sanitizes(self) -> None:
        long_message_id = "m-" + ("x" * 200)
        envelope = build_event_envelope(
            {"ticket_id": "t-999", "message_id": long_message_id, "group_id": "team alpha"}
        )

        self.assertEqual(envelope.conversation_id, "t-999")
        self.assertLessEqual(len(envelope.dedupe_id), 128)
        self.assertEqual(envelope.group_id, "team-alpha")
        self.assertTrue(envelope.event_id.startswith("evt:"))

    def test_kill_switch_cache_is_respected(self) -> None:
        now = time.time()
        worker._FLAG_CACHE.update(
            {"safe_mode": False, "automation_enabled": True, "expires_at": now + 60}
        )

        safe_mode, automation_enabled = worker._load_kill_switches()

        self.assertFalse(safe_mode)
        self.assertTrue(automation_enabled)
        self.assertGreater(worker._FLAG_CACHE["expires_at"], now)

    def test_idempotency_write_persists_expected_fields(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-321", "message_id": "m-321"})
        plan = plan_actions(envelope, safe_mode=True, automation_enabled=False)

        worker._persist_idempotency(envelope, plan)
        table = worker._table(os.environ["IDEMPOTENCY_TABLE_NAME"])
        self.assertEqual(len(table.items), 1)

        item = table.items[0]
        for field in [
            "event_id",
            "conversation_id",
            "mode",
            "status",
            "payload_excerpt",
            "safe_mode",
            "automation_enabled",
            "expires_at",
        ]:
            self.assertIn(field, item)
        self.assertEqual(item["status"], "processed")
        self.assertEqual(item["mode"], plan.mode)

    def test_execute_and_record_writes_state_and_audit_tables(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-555", "message_id": "m-555"})
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=False)

        worker._persist_idempotency(envelope, plan)
        worker._execute_and_record(envelope, plan)

        state_table = worker._table(os.environ["CONVERSATION_STATE_TABLE_NAME"])
        audit_table = worker._table(os.environ["AUDIT_TRAIL_TABLE_NAME"])

        self.assertEqual(len(state_table.items), 1)
        self.assertEqual(len(audit_table.items), 1)

        state_item = state_table.items[0]
        audit_item = audit_table.items[0]

        self.assertEqual(state_item["event_id"], envelope.event_id)
        self.assertIn("expires_at", state_item)
        self.assertIn("ts_action_id", audit_item)
        self.assertEqual(audit_item["event_id"], envelope.event_id)

    def test_plan_skips_order_status_when_safety_blocks(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-safe"})
        scenarios = [
            {"safe_mode": True, "automation_enabled": True},
            {"safe_mode": False, "automation_enabled": False},
        ]

        for scenario in scenarios:
            plan = plan_actions(
                envelope,
                safe_mode=scenario["safe_mode"],
                automation_enabled=scenario["automation_enabled"],
            )
            action_types = [action["type"] for action in plan.actions]
            self.assertNotIn("order_status_draft_reply", action_types)
            if scenario["safe_mode"]:
                self.assertEqual(plan.mode, "route_only")


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PipelineTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
