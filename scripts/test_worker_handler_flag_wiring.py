from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
SRC_STR = str(SRC)
# Keep SRC at the front of sys.path deterministically (no conditional that can be skipped)
sys.path = [SRC_STR] + [p for p in sys.path if p != SRC_STR]

# Ensure required env vars exist before importing the handler module.
os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "local-idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/local/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/local/automation_enabled")
os.environ.setdefault("CONVERSATION_STATE_TABLE_NAME", "local-conversation-state")
os.environ.setdefault("AUDIT_TRAIL_TABLE_NAME", "local-audit-trail")

from lambda_handlers.worker import handler as worker  # noqa: E402
from richpanel_middleware.automation.pipeline import ExecutionResult  # noqa: E402
from richpanel_middleware.automation.router import RoutingDecision  # noqa: E402
from richpanel_middleware.ingest.envelope import EventEnvelope  # noqa: E402


class WorkerHandlerFlagWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        # Keep tests offline/deterministic.
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update(
            {"safe_mode": True, "automation_enabled": False, "expires_at": 0.0}
        )
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None
        os.environ["RICHPANEL_OUTBOUND_ENABLED"] = "true"
        os.environ.pop("MW_ALLOW_NETWORK_READS", None)

    def test_plan_actions_receives_allow_network_and_outbound_flags(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-1",
            received_at="2024-01-01T00:00:00Z",
            group_id="group-1",
            dedupe_id="m1",
            payload={},
            source="test",
            conversation_id="c-1",
            message_id="m1",
        )
        fake_plan = mock.Mock()
        fake_plan.safe_mode = False
        fake_plan.automation_enabled = True
        fake_plan.mode = "automation_candidate"
        fake_plan.actions = []
        fake_execution = mock.Mock(dry_run=True)

        with mock.patch.object(
            worker, "_load_kill_switches", return_value=(False, True)
        ), mock.patch.object(
            worker, "normalize_event", return_value=envelope
        ), mock.patch.object(
            worker, "plan_actions", return_value=fake_plan
        ) as plan_mock, mock.patch.object(
            worker, "_persist_idempotency"
        ), mock.patch.object(
            worker, "_execute_and_record", return_value=fake_execution
        ), mock.patch.object(
            worker,
            "_maybe_execute_outbound_reply",
            return_value={"sent": False, "reason": "skipped"},
        ):
            event = {
                "Records": [
                    {
                        "messageId": "m1",
                        "body": json.dumps(
                            {"payload": {"ticket_id": "t-1", "message_id": "m1"}}
                        ),
                    }
                ]
            }
            worker.lambda_handler(event, None)

        plan_mock.assert_called_once_with(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
        )

    def test_plan_actions_receives_off_path_flags_when_outbound_disabled(self) -> None:
        os.environ["RICHPANEL_OUTBOUND_ENABLED"] = "false"
        envelope = EventEnvelope(
            event_id="evt-2",
            received_at="2024-01-01T00:00:00Z",
            group_id="group-2",
            dedupe_id="m2",
            payload={},
            source="test",
            conversation_id="c-2",
            message_id="m2",
        )
        fake_plan = mock.Mock()
        fake_plan.safe_mode = False
        fake_plan.automation_enabled = True
        fake_plan.mode = "automation_candidate"
        fake_plan.actions = []
        fake_execution = mock.Mock(dry_run=True)

        with mock.patch.object(
            worker, "_load_kill_switches", return_value=(False, True)
        ), mock.patch.object(
            worker, "normalize_event", return_value=envelope
        ), mock.patch.object(
            worker, "plan_actions", return_value=fake_plan
        ) as plan_mock, mock.patch.object(
            worker, "_persist_idempotency"
        ), mock.patch.object(
            worker, "_execute_and_record", return_value=fake_execution
        ), mock.patch.object(
            worker,
            "_maybe_execute_outbound_reply",
            return_value={"sent": False, "reason": "skipped"},
        ):
            event = {
                "Records": [
                    {
                        "messageId": "m2",
                        "body": json.dumps(
                            {"payload": {"ticket_id": "t-2", "message_id": "m2"}}
                        ),
                    }
                ]
            }
            worker.lambda_handler(event, None)

        plan_mock.assert_called_once_with(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            outbound_enabled=False,
        )

    def test_allow_network_enabled_when_shadow_reads_allowed(self) -> None:
        os.environ["RICHPANEL_OUTBOUND_ENABLED"] = "false"
        os.environ["MW_ALLOW_NETWORK_READS"] = "true"
        envelope = EventEnvelope(
            event_id="evt-3",
            received_at="2024-01-01T00:00:00Z",
            group_id="group-3",
            dedupe_id="m3",
            payload={},
            source="test",
            conversation_id="c-3",
            message_id="m3",
        )
        fake_plan = mock.Mock()
        fake_plan.safe_mode = False
        fake_plan.automation_enabled = True
        fake_plan.mode = "automation_candidate"
        fake_plan.actions = []
        fake_execution = mock.Mock(dry_run=True)

        with mock.patch.object(
            worker, "_load_kill_switches", return_value=(False, True)
        ), mock.patch.object(
            worker, "normalize_event", return_value=envelope
        ), mock.patch.object(
            worker, "plan_actions", return_value=fake_plan
        ) as plan_mock, mock.patch.object(
            worker, "_persist_idempotency"
        ), mock.patch.object(
            worker, "_execute_and_record", return_value=fake_execution
        ), mock.patch.object(
            worker,
            "_maybe_execute_outbound_reply",
            return_value={"sent": False, "reason": "skipped"},
        ):
            event = {
                "Records": [
                    {
                        "messageId": "m3",
                        "body": json.dumps(
                            {"payload": {"ticket_id": "t-3", "message_id": "m3"}}
                        ),
                    }
                ]
            }
            worker.lambda_handler(event, None)

        plan_mock.assert_called_once_with(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=False,
        )

    def test_record_openai_rewrite_evidence_updates_tables(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-9",
            received_at="2026-01-20T00:00:00Z",
            group_id="group-9",
            dedupe_id="dedupe-9",
            payload={},
            source="test",
            conversation_id="conv-9",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=[],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        execution = ExecutionResult(
            event_id="evt-9",
            mode="automation_candidate",
            dry_run=True,
            actions=[],
            routing=routing,
            state_record={},
            audit_record={"recorded_at": "2026-01-20T00:00:00Z"},
        )
        outbound_result = {
            "openai_rewrite": {
                "rewrite_attempted": True,
                "rewrite_applied": False,
                "model": "gpt-5.2-chat-latest",
                "response_id": None,
                "response_id_unavailable_reason": "dry_run",
                "fallback_used": True,
                "reason": "dry_run",
                "error_class": "OpenAIDryRun",
            }
        }
        table = mock.Mock()
        with mock.patch.object(worker, "_table", return_value=table):
            worker._record_openai_rewrite_evidence(
                envelope,
                execution,
                outbound_result=outbound_result,
            )

        self.assertGreaterEqual(table.update_item.call_count, 2)

    def test_record_openai_rewrite_evidence_uses_group_id_fallback(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-10",
            received_at="2026-01-20T00:00:00Z",
            group_id="group-10",
            dedupe_id="dedupe-10",
            payload={},
            source="test",
            conversation_id="",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=[],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        execution = ExecutionResult(
            event_id="evt-10",
            mode="automation_candidate",
            dry_run=True,
            actions=[],
            routing=routing,
            state_record={},
            audit_record={"recorded_at": "2026-01-20T00:00:00Z"},
        )
        outbound_result = {
            "openai_rewrite": {
                "rewrite_attempted": True,
                "rewrite_applied": False,
                "model": "gpt-5.2-chat-latest",
                "response_id": None,
                "response_id_unavailable_reason": "dry_run",
                "fallback_used": True,
                "reason": "dry_run",
                "error_class": "OpenAIDryRun",
            }
        }
        table = mock.Mock()
        with mock.patch.object(worker, "_table", return_value=table):
            worker._record_openai_rewrite_evidence(
                envelope,
                execution,
                outbound_result=outbound_result,
            )

        keys = [
            call.kwargs.get("Key", {}) for call in table.update_item.mock_calls
        ]
        self.assertTrue(any(key.get("conversation_id") == "group-10" for key in keys))

    def test_record_outbound_evidence_updates_tables(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-11",
            received_at="2026-01-20T00:00:00Z",
            group_id="group-11",
            dedupe_id="dedupe-11",
            payload={},
            source="test",
            conversation_id="conv-11",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=[],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        execution = ExecutionResult(
            event_id="evt-11",
            mode="automation_candidate",
            dry_run=True,
            actions=[],
            routing=routing,
            state_record={},
            audit_record={"recorded_at": "2026-01-20T00:00:00Z"},
        )
        outbound_result = {
            "sent": True,
            "reason": "sent",
            "responses": [
                {"action": "send_message", "status": 200, "dry_run": False},
                {"action": "add_tag", "status": 200, "dry_run": False},
            ],
        }
        table = mock.Mock()
        with mock.patch.object(worker, "_table", return_value=table):
            worker._record_outbound_evidence(
                envelope,
                execution,
                outbound_result=outbound_result,
            )

        self.assertGreaterEqual(table.update_item.call_count, 2)

    def test_record_outbound_evidence_uses_group_id_fallback(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-12",
            received_at="2026-01-20T00:00:00Z",
            group_id="group-12",
            dedupe_id="dedupe-12",
            payload={},
            source="test",
            conversation_id="",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=[],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        execution = ExecutionResult(
            event_id="evt-12",
            mode="automation_candidate",
            dry_run=True,
            actions=[],
            routing=routing,
            state_record={},
            audit_record={"recorded_at": "2026-01-20T00:00:00Z"},
        )
        outbound_result = {"sent": False, "reason": "send_message_failed", "responses": []}
        table = mock.Mock()
        with mock.patch.object(worker, "_table", return_value=table):
            worker._record_outbound_evidence(
                envelope,
                execution,
                outbound_result=outbound_result,
            )

        keys = [
            call.kwargs.get("Key", {}) for call in table.update_item.mock_calls
        ]
        self.assertTrue(any(key.get("conversation_id") == "group-12" for key in keys))

    def test_sanitize_outbound_responses_filters_and_coerces(self) -> None:
        responses = [
            {"action": "send_message", "status": "201", "dry_run": False},
            {"action": "add_tag", "status": 200.0, "dry_run": True},
            {"action": "noop", "status": "bad", "dry_run": "nope"},
            "bad",
        ]
        sanitized = worker._sanitize_outbound_responses(responses)
        self.assertEqual(len(sanitized), 3)
        self.assertEqual(sanitized[0]["status"], 201)
        self.assertEqual(sanitized[1]["status"], 200)
        self.assertIn("action", sanitized[2])
        self.assertNotIn("dry_run", sanitized[2])

    def test_resolve_outbound_evidence_handles_invalid(self) -> None:
        self.assertIsNone(worker._resolve_outbound_evidence("nope"))
        self.assertEqual(
            worker._resolve_outbound_evidence({"sent": "yes", "responses": "bad"}),
            {"sent": None, "reason": None, "responses": []},
        )

    def test_record_outbound_evidence_skips_when_invalid(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-13",
            received_at="2026-01-20T00:00:00Z",
            group_id="group-13",
            dedupe_id="dedupe-13",
            payload={},
            source="test",
            conversation_id="conv-13",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=[],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        execution = ExecutionResult(
            event_id="evt-13",
            mode="automation_candidate",
            dry_run=True,
            actions=[],
            routing=routing,
            state_record={},
            audit_record={"recorded_at": "2026-01-20T00:00:00Z"},
        )
        table = mock.Mock()
        with mock.patch.object(worker, "_table", return_value=table):
            worker._record_outbound_evidence(
                envelope, execution, outbound_result="not-a-dict"
            )
        table.update_item.assert_not_called()

    def test_record_outbound_evidence_skips_audit_without_recorded_at(self) -> None:
        envelope = EventEnvelope(
            event_id="evt-14",
            received_at="2026-01-20T00:00:00Z",
            group_id="group-14",
            dedupe_id="dedupe-14",
            payload={},
            source="test",
            conversation_id="conv-14",
        )
        routing = RoutingDecision(
            category="order_status",
            tags=[],
            reason="test",
            department="Email Support Team",
            intent="order_status_tracking",
        )
        execution = ExecutionResult(
            event_id="evt-14",
            mode="automation_candidate",
            dry_run=True,
            actions=[],
            routing=routing,
            state_record={},
            audit_record={},
        )
        outbound_result = {"sent": False, "reason": "send_message_failed", "responses": []}
        table = mock.Mock()
        with mock.patch.object(worker, "_table", return_value=table):
            worker._record_outbound_evidence(
                envelope,
                execution,
                outbound_result=outbound_result,
            )
        self.assertEqual(table.update_item.call_count, 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()  # pragma: no cover
