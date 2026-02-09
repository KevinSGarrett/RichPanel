from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock

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
    ActionPlan,
    execute_order_status_reply,
    EMAIL_SUPPORT_ROUTE_TAG,
    LOOP_PREVENTION_TAG,
    SKIP_FOLLOWUP_TAG,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from richpanel_middleware.integrations.richpanel.tickets import (  # noqa: E402
    TicketMetadata,
)


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        dry_run: bool = False,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.dry_run = dry_run
        self._payload = payload or {}

    def json(self) -> Dict[str, Any]:
        return dict(self._payload)


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def execute(
        self,
        method: str,
        path: str,
        json_body: Dict[str, Any] | None = None,
        dry_run: bool = False,
        log_body_excerpt: bool | None = None,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "json_body": json_body,
                "dry_run": dry_run,
                "log_body_excerpt": log_body_excerpt,
            }
        )
        return FakeResponse(status_code=200, dry_run=False, payload={"ticket": {"status": "CLOSED"}})


class EmailOutboundSendMessageTests(unittest.TestCase):
    def test_email_channel_uses_send_message_and_records_status(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "ticket-123",
                "channel": "email",
                "message": "Where is my order?",
                "customer_email": "allowed@example.com",
            }
        )
        plan = ActionPlan(
            event_id=envelope.event_id,
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {"draft_reply": {"body": "Here is your update."}},
                }
            ],
        )
        executor = FakeExecutor()

        with mock.patch.dict(
            os.environ,
            {
                "MW_OUTBOUND_ALLOWLIST_EMAILS": "allowed@example.com",
                "RICHPANEL_BOT_AGENT_ID": "agent-xyz",
            },
            clear=False,
        ), mock.patch(
            "richpanel_middleware.automation.pipeline._safe_ticket_snapshot_fetch",
            return_value=(
                TicketMetadata(status="open", tags=set(), status_code=200, dry_run=False),
                "email",
                "allowed@example.com",
            ),
        ), mock.patch(
            "richpanel_middleware.automation.pipeline._safe_ticket_metadata_fetch",
            return_value=TicketMetadata(status="closed", tags=set(), status_code=200, dry_run=False),
        ), mock.patch(
            "richpanel_middleware.automation.pipeline._safe_ticket_comment_operator_fetch",
            return_value=True,
        ), mock.patch(
            "richpanel_middleware.automation.pipeline.resolve_env_name",
            return_value=("dev", None),
        ):
            result = execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=executor,
            )

        send_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/send-message")
        ]
        self.assertEqual(1, len(send_calls))

        send_response_entries = [
            entry
            for entry in result.get("responses", [])
            if entry.get("action") == "send_message"
        ]
        self.assertTrue(send_response_entries)
        self.assertEqual(
            200,
            send_response_entries[0].get("status"),
        )

    def test_email_channel_missing_bot_agent_routes_support(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "ticket-456",
                "channel": "email",
                "message": "Where is my order?",
                "customer_email": "allowed@example.com",
            }
        )
        plan = ActionPlan(
            event_id=envelope.event_id,
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {"draft_reply": {"body": "Update."}},
                }
            ],
        )
        executor = FakeExecutor()

        with mock.patch.dict(
            os.environ,
            {"MW_OUTBOUND_ALLOWLIST_EMAILS": "allowed@example.com"},
            clear=False,
        ), mock.patch(
            "richpanel_middleware.automation.pipeline._safe_ticket_snapshot_fetch",
            return_value=(
                TicketMetadata(status="open", tags=set(), status_code=200, dry_run=False),
                "email",
                "allowed@example.com",
            ),
        ), mock.patch(
            "richpanel_middleware.automation.pipeline.resolve_env_name",
            return_value=("dev", None),
        ):
            result = execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=executor,
            )

        send_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/send-message")
        ]
        self.assertEqual(0, len(send_calls))
        self.assertEqual(result.get("blocked_reason"), "missing_bot_agent_id")

    def test_non_email_channel_does_not_use_send_message(self) -> None:
        envelope = build_event_envelope(
            {"ticket_id": "ticket-789", "channel": "chat", "message": "Status?"}
        )
        plan = ActionPlan(
            event_id=envelope.event_id,
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {"draft_reply": {"body": "Update."}},
                }
            ],
        )
        executor = FakeExecutor()

        with mock.patch.dict(
            os.environ,
            {"MW_OUTBOUND_ALLOWLIST_EMAILS": "allowed@example.com"},
            clear=False,
        ), mock.patch(
            "richpanel_middleware.automation.pipeline._safe_ticket_snapshot_fetch",
            return_value=(
                TicketMetadata(status="open", tags=set(), status_code=200, dry_run=False),
                "chat",
                None,
            ),
        ), mock.patch(
            "richpanel_middleware.automation.pipeline.resolve_env_name",
            return_value=("dev", None),
        ):
            execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=executor,
            )

        send_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/send-message")
        ]
        self.assertEqual(0, len(send_calls))

    def test_read_only_blocks_outbound(self) -> None:
        envelope = build_event_envelope(
            {"ticket_id": "ticket-999", "channel": "email", "message": "Status?"}
        )
        plan = ActionPlan(
            event_id=envelope.event_id,
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {"draft_reply": {"body": "Update."}},
                }
            ],
        )
        executor = FakeExecutor()

        with mock.patch.dict(
            os.environ,
            {"RICHPANEL_READ_ONLY": "true"},
            clear=False,
        ):
            result = execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=executor,
            )

        self.assertEqual(result.get("reason"), "read_only_guard")
        self.assertFalse(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )

    def test_followup_routes_support_without_reply(self) -> None:
        envelope = build_event_envelope(
            {"ticket_id": "ticket-321", "channel": "email", "message": "Follow-up"}
        )
        plan = ActionPlan(
            event_id=envelope.event_id,
            mode="automation_candidate",
            safe_mode=False,
            automation_enabled=True,
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {"draft_reply": {"body": "Update."}},
                }
            ],
        )
        executor = FakeExecutor()

        with mock.patch.dict(
            os.environ,
            {"MW_OUTBOUND_ALLOWLIST_EMAILS": "allowed@example.com"},
            clear=False,
        ), mock.patch(
            "richpanel_middleware.automation.pipeline._safe_ticket_snapshot_fetch",
            return_value=(
                TicketMetadata(
                    status="open",
                    tags={LOOP_PREVENTION_TAG},
                    status_code=200,
                    dry_run=False,
                ),
                "email",
                "allowed@example.com",
            ),
        ), mock.patch(
            "richpanel_middleware.automation.pipeline.resolve_env_name",
            return_value=("dev", None),
        ):
            result = execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=executor,
            )

        tag_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/add-tags")
        ]
        self.assertTrue(tag_calls)
        self.assertEqual(result.get("reason"), "followup_after_auto_reply")
        self.assertIn(EMAIL_SUPPORT_ROUTE_TAG, tag_calls[0]["json_body"]["tags"])
        self.assertIn(SKIP_FOLLOWUP_TAG, tag_calls[0]["json_body"]["tags"])


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(unittest.main())  # pragma: no cover - CLI entrypoint
