"""
Unit tests for the ticket-reopen behaviour in the followup_after_auto_reply path.

The bug: when a customer replies to a CLOSED ticket, pipeline.py detects the
mw-auto-replied loop-prevention tag and routes to Email Support, but never
reopened the ticket. Agents only see OPEN tickets so the follow-up was lost.

These tests verify that execute_order_status_reply() now issues a reopen call
(PUT /v1/tickets/{id} with state:open) before routing tags when ticket is CLOSED,
and does NOT issue the reopen call when the ticket is already OPEN.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "local-idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/local/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/local/automation_enabled")
os.environ.setdefault("CONVERSATION_STATE_TABLE_NAME", "local-conversation-state")
os.environ.setdefault("AUDIT_TRAIL_TABLE_NAME", "local-audit-trail")
os.environ.setdefault("CONVERSATION_STATE_TTL_SECONDS", "3600")
os.environ.setdefault("AUDIT_TRAIL_TTL_SECONDS", "3600")

from richpanel_middleware.automation.pipeline import (  # noqa: E402
    LOOP_PREVENTION_TAG,
    FOLLOWUP_REOPEN_TAG,
    execute_order_status_reply,
    ActionPlan,
)
from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelExecutor,
    RichpanelResponse,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402


def _ok_response(dry_run: bool = False) -> RichpanelResponse:
    return RichpanelResponse(
        status_code=200,
        headers={},
        body=b"{}",
        url="https://app.richpanel.com/v1/tickets/test-id",
        dry_run=dry_run,
    )


def _err_response() -> RichpanelResponse:
    return RichpanelResponse(
        status_code=500,
        headers={},
        body=b'{"error":"internal"}',
        url="https://app.richpanel.com/v1/tickets/test-id",
        dry_run=False,
    )


def _build_envelope(ticket_id: str = "test-conv-1") -> Any:
    return build_event_envelope(
        {
            "conversation_id": ticket_id,
            "ticket_id": ticket_id,
            "via": {"channel": "email"},
            "message": "Where is my order?",
        }
    )


def _build_plan() -> ActionPlan:
    return ActionPlan(
        event_id="evt-followup-reopen-test",
        mode="prod",
        safe_mode=False,
        automation_enabled=True,
        routing=mock.MagicMock(intent="order_status_tracking", category="order_status"),
        actions=[
            {
                "type": "order_status_draft_reply",
                "parameters": {
                    "draft_reply": {"body": "Your order will arrive in 1-2 days."},
                    "order_summary": {"order_id": "ORD-123"},
                },
            }
        ],
        reasons=[],
    )


def _make_executor(status: str) -> mock.MagicMock:
    executor = mock.MagicMock(spec=RichpanelExecutor)
    payload = {
        "status": status,
        "tags": [LOOP_PREVENTION_TAG, "mw-order-status-answered"],
        "via": {"channel": "email"},
        "customer": {"email": "customer@example.com"},
    }
    get_resp = RichpanelResponse(
        status_code=200,
        headers={},
        body=json.dumps(payload).encode(),
        url="https://app.richpanel.com/v1/tickets/test-conv-1",
        dry_run=False,
    )

    def side_effect(method: str, path: str, **kwargs: Any) -> RichpanelResponse:
        if method == "GET":
            return get_resp
        return _ok_response()

    executor.execute.side_effect = side_effect
    return executor


def _run(executor: mock.MagicMock, allow_network: bool = True) -> Dict[str, Any]:
    with mock.patch(
        "richpanel_middleware.automation.pipeline.resolve_env_name",
        return_value=("dev", "dev"),
    ):
        return execute_order_status_reply(
            _build_envelope(),
            _build_plan(),
            safe_mode=False,
            automation_enabled=True,
            allow_network=allow_network,
            outbound_enabled=allow_network,
            richpanel_executor=executor,
        )


class FollowupReopenTests(unittest.TestCase):
    def test_reopen_put_called_when_ticket_closed(self) -> None:
        """PUT /v1/tickets/{id} with state:open must be called when ticket is CLOSED."""
        executor = _make_executor("CLOSED")
        _run(executor)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        reopen_calls = [
            c
            for c in put_calls
            if "/add-tags" not in c.args[1]
            and c.kwargs.get("json_body", {}).get("ticket", {}).get("state") == "open"
        ]
        self.assertTrue(len(reopen_calls) >= 1, "Expected reopen PUT call but got none")

    def test_reopen_put_is_first_put_call(self) -> None:
        """Reopen must happen before routing tags are added."""
        executor = _make_executor("CLOSED")
        _run(executor)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        self.assertGreater(len(put_calls), 0)
        first_body = put_calls[0].kwargs.get("json_body", {})
        self.assertNotIn(
            "/add-tags",
            put_calls[0].args[1],
            "First PUT must be reopen, not add-tags",
        )
        self.assertEqual(first_body.get("ticket", {}).get("state"), "open")

    def test_routing_tags_added_after_reopen(self) -> None:
        """route-email-support-team tag must be added after reopening."""
        executor = _make_executor("CLOSED")
        _run(executor)

        all_tags: List[str] = []
        for c in executor.execute.call_args_list:
            if c.args[0] == "PUT" and "/add-tags" in c.args[1]:
                all_tags.extend(c.kwargs.get("json_body", {}).get("tags", []))

        self.assertIn("route-email-support-team", all_tags)

    def test_followup_reopen_audit_tag_added(self) -> None:
        """mw-followup-reopened audit tag must be applied after successful reopen."""
        executor = _make_executor("CLOSED")
        _run(executor)

        all_tags: List[str] = []
        for c in executor.execute.call_args_list:
            if c.args[0] == "PUT" and "/add-tags" in c.args[1]:
                all_tags.extend(c.kwargs.get("json_body", {}).get("tags", []))

        self.assertIn(FOLLOWUP_REOPEN_TAG, all_tags)

    def test_result_is_followup_not_sent(self) -> None:
        """Return must have sent=False and reason=followup_after_auto_reply."""
        executor = _make_executor("CLOSED")
        result = _run(executor)
        self.assertFalse(result.get("sent"))
        self.assertEqual(result.get("reason"), "followup_after_auto_reply")

    def test_no_reopen_when_ticket_already_open(self) -> None:
        """No reopen PUT when ticket is already OPEN."""
        executor = _make_executor("OPEN")
        _run(executor)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        reopen_calls = [
            c
            for c in put_calls
            if "/add-tags" not in c.args[1]
            and c.kwargs.get("json_body", {}).get("ticket", {}).get("state") == "open"
        ]
        self.assertEqual(
            len(reopen_calls), 0, "No reopen PUT when ticket is already OPEN"
        )

    def test_routing_tags_added_even_when_reopen_fails(self) -> None:
        """Routing tags must still be applied if the reopen PUT returns 500 (fail-open)."""
        executor = mock.MagicMock(spec=RichpanelExecutor)
        payload = {
            "status": "CLOSED",
            "tags": [LOOP_PREVENTION_TAG],
            "via": {"channel": "email"},
        }
        get_resp = RichpanelResponse(
            status_code=200,
            headers={},
            body=json.dumps(payload).encode(),
            url="https://app.richpanel.com/v1/tickets/test-conv-1",
            dry_run=False,
        )
        call_n = {"n": 0}

        def side_effect(method: str, path: str, **kwargs: Any) -> RichpanelResponse:
            if method == "GET":
                return get_resp
            call_n["n"] += 1
            return _err_response() if call_n["n"] == 1 else _ok_response()

        executor.execute.side_effect = side_effect
        result = _run(executor)

        all_tags: List[str] = []
        for c in executor.execute.call_args_list:
            if c.args[0] == "PUT" and "/add-tags" in c.args[1]:
                all_tags.extend(c.kwargs.get("json_body", {}).get("tags", []))

        self.assertIn("route-email-support-team", all_tags)
        self.assertFalse(result.get("sent"))

    def test_dry_run_reopen_uses_dry_run_true(self) -> None:
        """When allow_network=False, reopen PUT must carry dry_run=True."""
        executor = mock.MagicMock(spec=RichpanelExecutor)
        payload = {
            "status": "CLOSED",
            "tags": [LOOP_PREVENTION_TAG],
            "via": {"channel": "email"},
        }
        get_resp = RichpanelResponse(
            status_code=200,
            headers={},
            body=json.dumps(payload).encode(),
            url="https://app.richpanel.com/v1/tickets/test-conv-1",
            dry_run=True,
        )
        dry_resp = _ok_response(dry_run=True)

        def side_effect(method: str, path: str, **kwargs: Any) -> RichpanelResponse:
            return get_resp if method == "GET" else dry_resp

        executor.execute.side_effect = side_effect
        _run(executor, allow_network=False)

        put_calls = [c for c in executor.execute.call_args_list if c.args[0] == "PUT"]
        reopen_calls = [
            c
            for c in put_calls
            if "/add-tags" not in c.args[1]
            and c.kwargs.get("json_body", {}).get("ticket", {}).get("state") == "open"
        ]
        for c in reopen_calls:
            self.assertTrue(
                c.kwargs.get("dry_run"),
                "Reopen PUT must use dry_run=True when allow_network=False",
            )


if __name__ == "__main__":
    unittest.main()
