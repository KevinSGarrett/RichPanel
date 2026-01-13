from __future__ import annotations

import json
import os
import sys
import time
import unittest
from unittest import mock
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

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
    execute_order_status_reply,
    execute_routing_tags,
    execute_plan,
    normalize_event,
    plan_actions,
)
from richpanel_middleware.automation.router import RoutingDecision  # noqa: E402
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from lambda_handlers.worker import handler as worker  # noqa: E402
from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelExecutor,
    RichpanelResponse,
    RichpanelRequestError,
    TransportError,
)


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_float(v) for v in value)
    return False


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
        envelope = build_event_envelope(
            {"ticket_id": "t-789", "order_id": "ord-789", "message": "Where is my order?"}
        )
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
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertEqual(routing.intent, "order_status_tracking")
        self.assertEqual(routing.department, "Email Support Team")


    def test_plan_generates_tracking_present_draft_reply(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-track",
                "order_id": "ord-321",
                "tracking_number": "1Z999",
                "carrier": "UPS",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        order_actions = [action for action in plan.actions if action["type"] == "order_status_draft_reply"]
        self.assertEqual(len(order_actions), 1)
        draft_reply = order_actions[0]["parameters"].get("draft_reply", {})
        self.assertIn("body", draft_reply)
        self.assertIn("1Z999", draft_reply["body"])
        self.assertIn("UPS", draft_reply["body"])
        self.assertIn("Tracking link:", draft_reply["body"])
        self.assertNotIn("We'll send tracking as soon as it ships.", draft_reply["body"])

    def test_plan_generates_fallback_when_eta_missing(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-noeta",
                "order_id": "ord-noeta",
                "message": "Where is my order?",
                # No tracking number, shipping method, or order dates to compute ETA.
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        order_actions = [action for action in plan.actions if action["type"] == "order_status_draft_reply"]
        self.assertEqual(len(order_actions), 1)
        draft_reply = order_actions[0]["parameters"].get("draft_reply")

        self.assertIsNotNone(draft_reply)
        assert isinstance(draft_reply, dict)
        self.assertTrue(draft_reply.get("body"))
        self.assertNotIn("business day", draft_reply["body"].lower())
        self.assertNotIn("None", draft_reply["body"])

    def test_routing_classifies_returns(self) -> None:
        envelope = build_event_envelope(
            {"ticket_id": "t-return", "message": "I need a refund or exchange this order"}
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=False)

        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertEqual(routing.category, "returns")
        self.assertEqual(routing.department, "Returns Admin")
        self.assertIn(routing.intent, {"refund_request", "exchange_request"})
        self.assertIn(f"mw-intent-{routing.intent}", routing.tags)

    def test_routing_fallback_when_message_missing(self) -> None:
        envelope = build_event_envelope({"ticket_id": "t-nomsg"})
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=False)

        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertEqual(routing.intent, "unknown")
        self.assertEqual(routing.department, "Email Support Team")
        self.assertEqual(routing.category, "general")

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
        self.assertIn("routing", result.state_record)
        routing = cast(RoutingDecision, plan.routing)
        self.assertIsNotNone(routing)
        assert routing is not None
        self.assertEqual(result.state_record["routing"]["department"], routing.department)
        self.assertEqual(result.audit_record["routing"]["intent"], routing.intent)
        self.assertEqual(len(captured_state), 1)
        self.assertEqual(len(captured_audit), 1)

    def test_ddb_sanitize_converts_floats_to_decimals_and_strips_nan(self) -> None:
        source = {
            "score": 0.25,
            "nested": {
                "values": [1.1, {"inner": float("inf")}],
                "tuple": (2.5, {"nan": float("nan")}),
            },
            "set": {3.3, "keep"},
        }

        sanitized = worker._ddb_sanitize(source)

        self.assertIsInstance(sanitized["score"], Decimal)
        self.assertEqual(sanitized["score"], Decimal("0.25"))
        nested_values = sanitized["nested"]["values"]
        self.assertIsInstance(nested_values[0], Decimal)
        self.assertIsNone(nested_values[1]["inner"])
        tuple_values = sanitized["nested"]["tuple"]
        self.assertIsInstance(tuple_values[0], Decimal)
        self.assertIsNone(tuple_values[1]["nan"])
        self.assertIn(Decimal("3.3"), sanitized["set"])
        self.assertFalse(_contains_float(sanitized))

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

    def test_kill_switch_env_override_takes_precedence_and_skips_ssm(self) -> None:
        class _FakeSSM:
            def __init__(self) -> None:
                self.calls = 0

            def get_parameters(self, Names, WithDecryption=False):  # type: ignore[no-untyped-def]
                self.calls += 1
                return {
                    "Parameters": [
                        {"Name": os.environ["SAFE_MODE_PARAM"], "Value": "true"},
                        {"Name": os.environ["AUTOMATION_ENABLED_PARAM"], "Value": "true"},
                    ]
                }

        fake_ssm = _FakeSSM()
        worker.boto3 = object()  # type: ignore
        worker._SSM_CLIENT = fake_ssm  # type: ignore

        with mock.patch.dict(
            os.environ,
            {
                "MW_ALLOW_ENV_FLAG_OVERRIDE": "true",
                "MW_SAFE_MODE_OVERRIDE": "false",
                "MW_AUTOMATION_ENABLED_OVERRIDE": "false",
            },
            clear=False,
        ):
            safe_mode, automation_enabled = worker._load_kill_switches()

        self.assertFalse(safe_mode)
        self.assertFalse(automation_enabled)
        self.assertEqual(fake_ssm.calls, 0)

    def test_kill_switch_env_override_requires_both_vars_and_fails_closed_on_ssm_error(self) -> None:
        class _FailingSSM:
            def get_parameters(self, Names, WithDecryption=False):  # type: ignore[no-untyped-def]
                raise RuntimeError("ssm read blocked")

        worker.boto3 = object()  # type: ignore
        worker._SSM_CLIENT = _FailingSSM()  # type: ignore

        with mock.patch.dict(
            os.environ,
            {
                "MW_ALLOW_ENV_FLAG_OVERRIDE": "true",
                # Intentionally omit MW_SAFE_MODE_OVERRIDE to prove partial overrides don't apply.
                "MW_AUTOMATION_ENABLED_OVERRIDE": "true",
            },
            clear=False,
        ):
            safe_mode, automation_enabled = worker._load_kill_switches()

        self.assertTrue(safe_mode)
        self.assertFalse(automation_enabled)

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
            "payload_fingerprint",
            "payload_field_count",
            "safe_mode",
            "automation_enabled",
            "expires_at",
        ]:
            self.assertIn(field, item)
        self.assertEqual(item["status"], "processed")
        self.assertEqual(item["mode"], plan.mode)
        self.assertGreater(len(item["payload_fingerprint"]), 0)
        self.assertEqual(item["payload_field_count"], len(envelope.payload))

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
        self.assertIn("routing", state_item)
        self.assertEqual(state_item["routing"]["department"], "Email Support Team")
        self.assertEqual(audit_item["routing"]["intent"], "unknown")

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


    def test_state_and_audit_redact_customer_body(self) -> None:
        envelope = build_event_envelope(
            {"ticket_id": "t-pii", "message": "Sensitive PII content should not persist"}
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=False)

        worker._persist_idempotency(envelope, plan)
        worker._execute_and_record(envelope, plan)

        idempotency_items = worker._table(os.environ["IDEMPOTENCY_TABLE_NAME"]).items
        state_items = worker._table(os.environ["CONVERSATION_STATE_TABLE_NAME"]).items
        audit_items = worker._table(os.environ["AUDIT_TRAIL_TABLE_NAME"]).items

        combined = json.dumps([idempotency_items, state_items, audit_items], default=str)
        self.assertNotIn("Sensitive PII content", combined)


class OutboundOrderStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update({"safe_mode": True, "automation_enabled": False, "expires_at": 0.0})
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None
        os.environ.pop("RICHPANEL_OUTBOUND_ENABLED", None)

    def _build_order_status_plan(self) -> tuple[Any, Any]:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-outbound",
                "order_id": "ord-123",
                "shipping_method": "2 business days",
                "created_at": "2024-12-20T00:00:00Z",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)
        return envelope, plan

    def test_outbound_skip_when_disabled(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor()

        result = execute_order_status_reply(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=False,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertFalse(result["sent"])
        self.assertEqual(len(executor.calls), 0)

    def test_outbound_executes_when_enabled(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor()

        result = execute_order_status_reply(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertTrue(result["sent"])
        self.assertEqual(len(executor.calls), 3)

        get_call = executor.calls[0]
        self.assertEqual(get_call["method"], "GET")
        self.assertIn("/v1/tickets/", get_call["path"])
        self.assertNotIn("/add-tags", get_call["path"])

        tag_call = executor.calls[1]
        self.assertEqual(tag_call["method"], "PUT")
        self.assertIn("/add-tags", tag_call["path"])
        self.assertEqual(
            set(tag_call["kwargs"]["json_body"]["tags"]),
            {"mw-auto-replied", "mw-order-status-answered"},
        )
        self.assertFalse(tag_call["kwargs"]["dry_run"])

        reply_call = executor.calls[2]
        self.assertEqual(reply_call["kwargs"]["json_body"]["status"], "resolved")
        self.assertIn("comment", reply_call["kwargs"]["json_body"])
        self.assertEqual(reply_call["kwargs"]["json_body"]["comment"]["type"], "public")
        self.assertFalse(reply_call["kwargs"]["dry_run"])

    def test_outbound_skips_when_ticket_already_resolved(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_status="resolved")

        result = execute_order_status_reply(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "already_resolved")
        self.assertEqual(len(executor.calls), 2)
        self.assertEqual(executor.calls[0]["method"], "GET")
        route_call = executor.calls[1]
        self.assertEqual(route_call["method"], "PUT")
        self.assertIn("/add-tags", route_call["path"])
        tags = route_call["kwargs"]["json_body"]["tags"]
        self.assertIn("route-email-support-team", tags)
        self.assertIn("mw-skip-order-status-closed", tags)

    def test_outbound_followup_after_auto_reply_routes_to_email_support(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_status="open", ticket_tags=["mw-auto-replied"])

        result = execute_order_status_reply(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertTrue(result["sent"])
        self.assertEqual(len(executor.calls), 3)
        self.assertEqual(executor.calls[0]["method"], "GET")
        tag_call = executor.calls[1]
        self.assertEqual(tag_call["method"], "PUT")
        self.assertIn("/add-tags", tag_call["path"])
        self.assertIn("mw-order-status-answered", tag_call["kwargs"]["json_body"]["tags"])
        reply_call = executor.calls[2]
        self.assertEqual(reply_call["method"], "PUT")
        self.assertEqual(reply_call["kwargs"]["json_body"]["status"], "resolved")
        self.assertNotIn("route-email-support-team", tag_call["kwargs"]["json_body"]["tags"])
        self.assertNotIn("mw-skip-followup-after-auto-reply", tag_call["kwargs"]["json_body"]["tags"])
        self.assertNotIn("mw-escalated-human", tag_call["kwargs"]["json_body"]["tags"])

    def test_outbound_status_read_failure_routes_to_email_support(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(raise_on_get=True)

        result = execute_order_status_reply(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "status_read_failed")
        self.assertEqual(len(executor.calls), 2)
        route_call = executor.calls[1]
        tags = route_call["kwargs"]["json_body"]["tags"]
        self.assertIn("route-email-support-team", tags)
        self.assertIn("mw-skip-status-read-failed", tags)

    def test_outbound_logging_does_not_emit_reply_body(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor()

        # Extract the draft reply text for assertion.
        action = [action for action in plan.actions if action.get("type") == "order_status_draft_reply"][0]
        reply_body = action["parameters"].get("draft_reply", {}).get("body", "")

        with self.assertLogs("richpanel_middleware.automation.pipeline", level="INFO") as captured:
            execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=cast(RichpanelExecutor, executor),
            )

        combined_logs = " ".join(captured.output)
        self.assertNotIn(reply_body, combined_logs)


class _RecordingExecutor:
    def __init__(
        self, *, ticket_status: str = "open", ticket_tags: list[str] | None = None, raise_on_get: bool = False
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.ticket_status = ticket_status
        self.ticket_tags = ticket_tags or []
        self.raise_on_get = raise_on_get

    def execute(self, method: str, path: str, **kwargs: Any) -> RichpanelResponse:
        self.calls.append({"method": method, "path": path, "kwargs": kwargs})

        if method.upper() == "GET" and path.startswith("/v1/tickets/") and "/add-tags" not in path:
            if self.raise_on_get:
                raise TransportError("simulated ticket read failure")
            body = json.dumps({"status": self.ticket_status, "tags": self.ticket_tags}).encode("utf-8")
            return RichpanelResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=body,
                url=path,
                dry_run=kwargs.get("dry_run", False),
            )

        return RichpanelResponse(
            status_code=202,
            headers={},
            body=b"",
            url=path,
            dry_run=kwargs.get("dry_run", False),
        )





class OutboundRoutingTagsTests(unittest.TestCase):
    def setUp(self) -> None:
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update({"safe_mode": True, "automation_enabled": False, "expires_at": 0.0})
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None
        os.environ.pop("RICHPANEL_OUTBOUND_ENABLED", None)

    def _build_routing_plan(self) -> tuple[Any, Any]:
        envelope = build_event_envelope(
            {"ticket_id": "t-route", "message": "I need a refund for my order"}
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)
        return envelope, plan

    def test_routing_tags_skip_when_outbound_disabled(self) -> None:
        envelope, plan = self._build_routing_plan()
        executor = _RecordingExecutor()

        result = execute_routing_tags(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=False,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertFalse(result["applied"])
        self.assertEqual(len(executor.calls), 0)

    def test_routing_tags_executes_when_enabled(self) -> None:
        envelope, plan = self._build_routing_plan()
        executor = _RecordingExecutor()

        result = execute_routing_tags(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=cast(RichpanelExecutor, executor),
        )

        self.assertTrue(result["applied"])
        self.assertEqual(len(executor.calls), 1)

        call = executor.calls[0]
        self.assertEqual(call["method"], "PUT")
        self.assertIn("/add-tags", call["path"])
        tags = call["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-routing-applied", tags)
        self.assertTrue(any(str(tag).startswith("mw-intent-") for tag in tags))
        self.assertFalse(call["kwargs"]["dry_run"])


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PipelineTests)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(OutboundOrderStatusTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(OutboundRoutingTagsTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
