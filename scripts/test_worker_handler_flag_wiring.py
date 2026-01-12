from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Ensure required env vars exist before importing the handler module.
os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "local-idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/local/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/local/automation_enabled")
os.environ.setdefault("CONVERSATION_STATE_TABLE_NAME", "local-conversation-state")
os.environ.setdefault("AUDIT_TRAIL_TABLE_NAME", "local-audit-trail")

from lambda_handlers.worker import handler as worker  # noqa: E402


class WorkerHandlerFlagWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        # Keep tests offline/deterministic.
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update({"safe_mode": True, "automation_enabled": False, "expires_at": 0.0})
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None
        os.environ["RICHPANEL_OUTBOUND_ENABLED"] = "true"

    def test_plan_actions_receives_allow_network_and_outbound_flags(self) -> None:
        envelope = SimpleNamespace(
            event_id="evt-1",
            conversation_id="c-1",
            payload={},
            message_id="m1",
            dedupe_id="m1",
            group_id=None,
            source="test",
            received_at="2024-01-01T00:00:00Z",
        )
        fake_plan = mock.Mock()
        fake_plan.safe_mode = False
        fake_plan.automation_enabled = True
        fake_plan.mode = "automation_candidate"
        fake_plan.actions = []
        fake_execution = mock.Mock(dry_run=True)

        with mock.patch.object(worker, "_load_kill_switches", return_value=(False, True)), mock.patch.object(
            worker, "normalize_event", return_value=envelope
        ), mock.patch.object(worker, "plan_actions", return_value=fake_plan) as plan_mock, mock.patch.object(
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
                        "body": json.dumps({"payload": {"ticket_id": "t-1", "message_id": "m1"}}),
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
        envelope = SimpleNamespace(
            event_id="evt-2",
            conversation_id="c-2",
            payload={},
            message_id="m2",
            dedupe_id="m2",
            group_id=None,
            source="test",
            received_at="2024-01-01T00:00:00Z",
        )
        fake_plan = mock.Mock()
        fake_plan.safe_mode = False
        fake_plan.automation_enabled = True
        fake_plan.mode = "automation_candidate"
        fake_plan.actions = []
        fake_execution = mock.Mock(dry_run=True)

        with mock.patch.object(worker, "_load_kill_switches", return_value=(False, True)), mock.patch.object(
            worker, "normalize_event", return_value=envelope
        ), mock.patch.object(worker, "plan_actions", return_value=fake_plan) as plan_mock, mock.patch.object(
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
                        "body": json.dumps({"payload": {"ticket_id": "t-2", "message_id": "m2"}}),
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
