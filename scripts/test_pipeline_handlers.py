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

from richpanel_middleware.automation import pipeline as pipeline_module  # noqa: E402
from richpanel_middleware.automation.pipeline import (  # noqa: E402
    execute_order_status_reply,
    execute_routing_tags,
    execute_plan,
    normalize_event,
    plan_actions,
    build_no_tracking_reply,
    _fingerprint_reply_body,
    _extract_customer_email_from_payload,
    _match_allowlist_email,
    _parse_allowlist_entries,
    _safe_ticket_snapshot_fetch,
    _extract_bot_agent_id,
    _load_secret_value,
    _read_only_guard_active,
    _SECRET_VALUE_CACHE,
    _SECRET_VALUE_CACHE_TTL_SECONDS,
    _resolve_bot_agent_id,
    _latest_comment_is_operator,
    _comment_operator_flag,
    _comment_created_at,
    _latest_comment_entry,
    _safe_ticket_comment_operator_fetch,
)
from richpanel_middleware.automation.llm_reply_rewriter import (  # noqa: E402
    ReplyRewriteResult,
)
from richpanel_middleware.automation.order_status_intent import (  # noqa: E402
    OrderStatusIntentArtifact,
    OrderStatusIntentResult,
)
from richpanel_middleware.automation.router import RoutingDecision  # noqa: E402
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from lambda_handlers.worker import handler as worker  # noqa: E402
from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelExecutor,
    RichpanelResponse,
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


def _accepted_intent_artifact() -> OrderStatusIntentArtifact:
    return OrderStatusIntentArtifact(
        result=OrderStatusIntentResult(
            is_order_status=True,
            confidence=0.95,
            reason="stubbed",
            extracted_order_number=None,
            language="en",
        ),
        llm_called=False,
        model="gpt-test",
        response_id=None,
        response_id_unavailable_reason="stubbed",
        confidence_threshold=0.85,
        accepted=True,
    )


class FingerprintReplyBodyTests(unittest.TestCase):
    def test_fingerprint_reply_body_none(self) -> None:
        self.assertIsNone(_fingerprint_reply_body(None))

    def test_fingerprint_reply_body_empty_string(self) -> None:
        self.assertIsNone(_fingerprint_reply_body(""))

    def test_fingerprint_reply_body_unicode(self) -> None:
        result = _fingerprint_reply_body("Hello 世界 🌍")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_fingerprint_reply_body_deterministic(self) -> None:
        body = "Test reply body"
        self.assertEqual(_fingerprint_reply_body(body), _fingerprint_reply_body(body))

    def test_fingerprint_reply_body_different_inputs(self) -> None:
        self.assertNotEqual(
            _fingerprint_reply_body("Body A"), _fingerprint_reply_body("Body B")
        )


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        # Reset worker caches so each test is deterministic and offline-safe.
        intent_patcher = mock.patch(
            "richpanel_middleware.automation.pipeline.classify_order_status_intent",
            return_value=_accepted_intent_artifact(),
        )
        intent_patcher.start()
        self.addCleanup(intent_patcher.stop)
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update(
            {"safe_mode": True, "automation_enabled": False, "expires_at": 0.0}
        )
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None

    def test_normalize_event_populates_defaults(self) -> None:
        envelope = normalize_event(
            {"payload": {"ticket_id": "t-123", "message_id": "m-1"}}
        )

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
            {
                "ticket_id": "t-789",
                "order_id": "ord-789",
                "created_at": "2025-01-01T00:00:00Z",
                "shipping_method": "2 business days",
                "message": "Where is my order?",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)

        self.assertEqual(plan.mode, "automation_candidate")
        self.assertEqual(plan.actions[0]["type"], "analyze")
        order_actions = [
            action
            for action in plan.actions
            if action["type"] == "order_status_draft_reply"
        ]
        self.assertEqual(len(order_actions), 1)
        order_action = order_actions[0]
        self.assertFalse(order_action["enabled"])
        self.assertTrue(order_action["dry_run"])
        self.assertIn("order_summary", order_action["parameters"])
        self.assertIn("prompt_fingerprint", order_action["parameters"])
        self.assertEqual(
            order_action["parameters"]["order_summary"]["order_id"], "ord-789"
        )
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
                "created_at": "2025-01-01T00:00:00Z",
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
        self.assertIn("1Z999", draft_reply["body"])
        self.assertIn("UPS", draft_reply["body"])
        self.assertIn("Tracking link:", draft_reply["body"])
        self.assertNotIn(
            "We'll send tracking as soon as it ships.", draft_reply["body"]
        )

    def test_no_tracking_reply_includes_remaining_window(self) -> None:
        inquiry_date = "2024-01-03"
        order_summary = {
            "order_id": "ord-no-track",
            "order_created_at": "2024-01-01",
            "shipping_method": "Standard",
        }

        reply = build_no_tracking_reply(order_summary, inquiry_date=inquiry_date)

        self.assertIsNotNone(reply)
        assert reply is not None
        self.assertEqual(reply["eta_human"], "1-3 business days")
        body_lower = reply["body"].lower()
        self.assertIn("1-3 business days", body_lower)
        self.assertIn("standard (3-5 business days)", body_lower)

    def test_plan_suppresses_when_order_context_missing(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-noeta",
                "message": "Where is my order?",
                # No tracking number, shipping method, or order dates to compute ETA.
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

    def test_plan_generates_eta_reply_when_context_present(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-eta",
                "order_id": "ord-eta",
                "created_at": "2025-01-01T00:00:00Z",
                "shipping_method": "Standard 3-5 business days",
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
        self.assertTrue(draft_reply["body"])

    def test_routing_classifies_returns(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-return",
                "message": "I need a refund or exchange this order",
            }
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
        self.assertEqual(
            result.state_record["routing"]["department"], routing.department
        )
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
            {
                "ticket_id": "t-999",
                "message_id": long_message_id,
                "group_id": "team alpha",
            }
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
                        {
                            "Name": os.environ["AUTOMATION_ENABLED_PARAM"],
                            "Value": "true",
                        },
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

    def test_kill_switch_env_override_requires_both_vars_and_fails_closed_on_ssm_error(
        self,
    ) -> None:
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
            {
                "ticket_id": "t-pii",
                "message": "Sensitive PII content should not persist",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=False)

        worker._persist_idempotency(envelope, plan)
        worker._execute_and_record(envelope, plan)

        idempotency_items = worker._table(os.environ["IDEMPOTENCY_TABLE_NAME"]).items
        state_items = worker._table(os.environ["CONVERSATION_STATE_TABLE_NAME"]).items
        audit_items = worker._table(os.environ["AUDIT_TRAIL_TABLE_NAME"]).items

        combined = json.dumps(
            [idempotency_items, state_items, audit_items], default=str
        )
        self.assertNotIn("Sensitive PII content", combined)


class OutboundOrderStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        intent_patcher = mock.patch(
            "richpanel_middleware.automation.pipeline.classify_order_status_intent",
            return_value=_accepted_intent_artifact(),
        )
        intent_patcher.start()
        self.addCleanup(intent_patcher.stop)
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update(
            {"safe_mode": True, "automation_enabled": False, "expires_at": 0.0}
        )
        worker._TABLE_CACHE.clear()
        worker._DDB_RESOURCE = None
        worker._SSM_CLIENT = None
        os.environ.pop("RICHPANEL_OUTBOUND_ENABLED", None)
        os.environ.pop("RICHPANEL_BOT_AGENT_ID", None)
        os.environ.pop("MW_OUTBOUND_ALLOWLIST_EMAILS", None)
        os.environ.pop("MW_OUTBOUND_ALLOWLIST_DOMAINS", None)
        os.environ.pop("RICHPANEL_ENV", None)
        os.environ.pop("RICH_PANEL_ENV", None)
        os.environ.pop("MW_ENV", None)
        os.environ.pop("ENV", None)
        os.environ.pop("ENVIRONMENT", None)

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

    def test_outbound_non_email_uses_comment_path(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_channel="chat")

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
        self.assertEqual(len(executor.calls), 4)
        self.assertFalse(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )

    def test_outbound_channel_prefers_webhook_payload(self) -> None:
        envelope, plan = self._build_order_status_plan()
        if isinstance(envelope.payload, dict):
            envelope.payload["channel"] = "chat"
        executor = _RecordingExecutor(ticket_channel="email")

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-123"}, clear=False
        ):
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
        self.assertFalse(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )

    def test_outbound_email_send_message_path(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_channel="email")

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-123"}, clear=False
        ):
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
        responses = result.get("responses") or []
        send_response = next(
            (entry for entry in responses if entry.get("action") == "send_message"),
            None,
        )
        self.assertIsNotNone(send_response)
        self.assertEqual(send_response.get("status"), 200)
        send_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/send-message")
        ]
        self.assertEqual(len(send_calls), 1)
        send_call = send_calls[0]
        send_index = executor.calls.index(send_call)
        self.assertEqual(
            send_call["kwargs"]["json_body"].get("author_id"), "agent-123"
        )
        verify_calls = [
            (idx, call)
            for idx, call in enumerate(executor.calls)
            if call["method"] == "GET"
            and call["path"].startswith("/v1/tickets/")
            and "/add-tags" not in call["path"]
            and idx > send_index
        ]
        self.assertTrue(verify_calls)
        verify_index = verify_calls[0][0]
        close_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT"
            and call["path"].startswith("/v1/tickets/")
            and "/send-message" not in call["path"]
            and "/add-tags" not in call["path"]
        ]
        self.assertTrue(close_calls)
        close_call = close_calls[0]
        close_payload = close_call["kwargs"]["json_body"]
        self.assertFalse(_payload_contains_comment(close_payload))
        add_tag_calls = [
            call for call in executor.calls if "/add-tags" in call["path"]
        ]
        self.assertEqual(len(add_tag_calls), 1)
        tags_payload = add_tag_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-outbound-path-send-message", tags_payload)
        self.assertLess(send_index, verify_index)
        self.assertLess(verify_index, executor.calls.index(close_call))
        self.assertLess(
            executor.calls.index(close_call), executor.calls.index(add_tag_calls[0])
        )

    def test_outbound_email_author_resolution_role_match(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_channel="email")

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-1"}, clear=False
        ):
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
        send_call = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/send-message")
        ][0]
        self.assertEqual(send_call["kwargs"]["json_body"].get("author_id"), "agent-1")
        self.assertFalse(
            any(
                call["method"] == "GET" and call["path"].startswith("/v1/users")
                for call in executor.calls
            )
        )

    def test_outbound_email_author_resolution_falls_back_to_first(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_channel="email")

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-123"}, clear=False
        ):
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
        send_call = [
            call
            for call in executor.calls
            if call["method"] == "PUT" and call["path"].endswith("/send-message")
        ][0]
        self.assertEqual(send_call["kwargs"]["json_body"].get("author_id"), "agent-123")

    def test_outbound_email_close_failure_routes_with_loop_tag(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="email",
            reply_status_codes=[500, 500],
            send_message_status_codes=[200],
        )

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-123"}, clear=False
        ):
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
        self.assertEqual(result["reason"], "reply_close_failed")
        tag_calls = [call for call in executor.calls if "/add-tags" in call["path"]]
        self.assertEqual(len(tag_calls), 1)
        tags = tag_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-auto-replied", tags)
        self.assertIn("mw-reply-sent", tags)
        self.assertIn("mw-outbound-path-send-message", tags)
        self.assertIn("mw-send-message-close-failed", tags)
        self.assertIn("route-email-support-team", tags)
        self.assertIn("mw-escalated-human", tags)

    def test_outbound_email_missing_author_id_routes_to_support(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(ticket_channel="email", users=[])

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
        self.assertEqual(result["reason"], "missing_bot_agent_id")
        self.assertFalse(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )
        close_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT"
            and call["path"].startswith("/v1/tickets/")
            and "/send-message" not in call["path"]
            and "/add-tags" not in call["path"]
        ]
        self.assertEqual(close_calls, [])
        route_calls = [
            call for call in executor.calls if "/add-tags" in call["path"]
        ]
        self.assertEqual(len(route_calls), 1)
        route_tags = route_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("route-email-support-team", route_tags)
        self.assertIn("mw-outbound-blocked-missing-bot-author", route_tags)
        self.assertIn("mw-escalated-human", route_tags)

    def test_outbound_email_operator_missing_routes_to_support(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="email", send_message_operator_flag=False
        )

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-123"}, clear=False
        ):
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
        self.assertEqual(result["reason"], "send_message_operator_missing")
        self.assertTrue(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )
        close_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT"
            and call["path"].startswith("/v1/tickets/")
            and "/send-message" not in call["path"]
            and "/add-tags" not in call["path"]
        ]
        self.assertEqual(close_calls, [])
        route_calls = [
            call for call in executor.calls if "/add-tags" in call["path"]
        ]
        self.assertEqual(len(route_calls), 1)
        route_tags = route_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-auto-replied", route_tags)
        self.assertIn("mw-order-status-answered", route_tags)
        self.assertIn("mw-reply-sent", route_tags)
        self.assertIn("mw-outbound-path-send-message", route_tags)
        self.assertIn("mw-send-message-operator-missing", route_tags)
        self.assertIn("route-email-support-team", route_tags)

    def test_outbound_email_send_message_failure_does_not_close(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="email", send_message_status_codes=[500]
        )

        with mock.patch.dict(
            os.environ, {"RICHPANEL_BOT_AGENT_ID": "agent-123"}, clear=False
        ):
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
        self.assertEqual(result["reason"], "send_message_failed")
        self.assertTrue(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )
        close_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT"
            and call["path"].startswith("/v1/tickets/")
            and "/send-message" not in call["path"]
            and "/add-tags" not in call["path"]
        ]
        self.assertEqual(close_calls, [])
        route_calls = [
            call for call in executor.calls if "/add-tags" in call["path"]
        ]
        self.assertEqual(len(route_calls), 1)
        route_tags = route_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-send-message-failed", route_tags)
        self.assertIn("route-email-support-team", route_tags)

    def test_latest_comment_operator_handles_mixed_timezones(self) -> None:
        comments = [
            {"created_at": "2026-01-01T01:00:00Z", "is_operator": True},
            {"created_at": "2026-01-01T02:00:00", "is_operator": False},
        ]
        self.assertFalse(_latest_comment_is_operator(comments))

    def test_comment_operator_flag_parses_numeric_and_string(self) -> None:
        self.assertTrue(_comment_operator_flag({"is_operator": 1}))
        self.assertFalse(_comment_operator_flag({"is_operator": 0}))
        self.assertTrue(_comment_operator_flag({"isOperator": "true"}))
        self.assertFalse(_comment_operator_flag({"isOperator": "false"}))

    def test_comment_created_at_handles_invalid_and_naive(self) -> None:
        self.assertIsNone(_comment_created_at({"created_at": "not-a-date"}))
        parsed = _comment_created_at({"created_at": "2026-01-01T01:00:00"})
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertIsNotNone(parsed.tzinfo)

    def test_latest_comment_entry_falls_back_to_last_dict(self) -> None:
        comments = [
            "bad",
            {"body": "first"},
            {"body": "last"},
        ]
        latest = _latest_comment_entry(comments)
        self.assertEqual(latest, {"body": "last"})

    def test_safe_ticket_comment_operator_fetch_handles_dry_run(self) -> None:
        class _DryRunExecutor:
            def execute(self, *_args: Any, **_kwargs: Any) -> RichpanelResponse:
                return RichpanelResponse(
                    status_code=200,
                    headers={},
                    body=b"{}",
                    url="/v1/tickets/123",
                    dry_run=True,
                )

        self.assertIsNone(
            _safe_ticket_comment_operator_fetch(
                "ticket-1",
                executor=cast(RichpanelExecutor, _DryRunExecutor()),
                allow_network=True,
            )
        )

    def test_safe_ticket_comment_operator_fetch_handles_non_200(self) -> None:
        class _ErrorExecutor:
            def execute(self, *_args: Any, **_kwargs: Any) -> RichpanelResponse:
                return RichpanelResponse(
                    status_code=500,
                    headers={},
                    body=b"{}",
                    url="/v1/tickets/123",
                    dry_run=False,
                )

        self.assertIsNone(
            _safe_ticket_comment_operator_fetch(
                "ticket-1",
                executor=cast(RichpanelExecutor, _ErrorExecutor()),
                allow_network=True,
            )
        )

    def test_safe_ticket_comment_operator_fetch_reads_wrapped_ticket(self) -> None:
        class _WrappedExecutor:
            def execute(self, *_args: Any, **_kwargs: Any) -> RichpanelResponse:
                payload = {
                    "ticket": {
                        "comments": [
                            {"created_at": "2026-01-01T00:00:00Z", "is_operator": True}
                        ]
                    }
                }
                return RichpanelResponse(
                    status_code=200,
                    headers={"content-type": "application/json"},
                    body=json.dumps(payload).encode("utf-8"),
                    url="/v1/tickets/123",
                    dry_run=False,
                )

        self.assertTrue(
            _safe_ticket_comment_operator_fetch(
                "ticket-1",
                executor=cast(RichpanelExecutor, _WrappedExecutor()),
                allow_network=True,
            )
        )

    def test_outbound_email_missing_bot_author_in_prod_blocks(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="email",
            ticket_customer_email="allow@example.com",
            users=[{"id": "agent-1", "role": "agent"}],
        )

        with mock.patch.dict(
            os.environ,
            {
                "MW_ENV": "prod",
                "SHOPIFY_SHOP_DOMAIN": "test-shop.myshopify.com",
                "MW_OUTBOUND_ALLOWLIST_EMAILS": "allow@example.com",
                "RICHPANEL_BOT_AGENT_ID": "",
            },
            clear=False,
        ):
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
        self.assertEqual(result["reason"], "read_only_guard")
        self.assertEqual(len(executor.calls), 0)

    def test_outbound_email_allowlist_blocks_in_prod_when_unset(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="email",
            ticket_customer_email="customer@example.com",
        )

        with mock.patch.dict(
            os.environ,
            {"MW_ENV": "prod", "SHOPIFY_SHOP_DOMAIN": "test-shop.myshopify.com"},
            clear=False,
        ):
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
        self.assertEqual(result["reason"], "read_only_guard")
        self.assertEqual(len(executor.calls), 0)

    def test_outbound_email_allowlist_blocks_in_non_prod_when_set(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="email",
            ticket_customer_email="blocked@example.com",
        )

        with mock.patch.dict(
            os.environ, {"MW_OUTBOUND_ALLOWLIST_EMAILS": "allow@example.com"}, clear=False
        ):
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
        self.assertEqual(result["reason"], "allowlist_blocked")
        self.assertFalse(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )
        route_calls = [
            call for call in executor.calls if "/add-tags" in call["path"]
        ]
        self.assertEqual(len(route_calls), 1)
        route_tags = route_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-outbound-blocked-allowlist", route_tags)
        self.assertIn("route-email-support-team", route_tags)

    def test_outbound_allowlist_blocks_non_email_channel(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_channel="chat",
            ticket_customer_email="blocked@example.com",
        )

        with mock.patch.dict(
            os.environ, {"MW_OUTBOUND_ALLOWLIST_EMAILS": "allow@example.com"}, clear=False
        ):
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
        self.assertEqual(result["reason"], "allowlist_blocked")
        self.assertFalse(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )
        close_calls = [
            call
            for call in executor.calls
            if call["method"] == "PUT"
            and call["path"].startswith("/v1/tickets/")
            and "/send-message" not in call["path"]
            and "/add-tags" not in call["path"]
        ]
        self.assertEqual(close_calls, [])
        route_calls = [
            call for call in executor.calls if "/add-tags" in call["path"]
        ]
        self.assertEqual(len(route_calls), 1)
        route_tags = route_calls[0]["kwargs"]["json_body"]["tags"]
        self.assertIn("mw-outbound-blocked-allowlist", route_tags)
        self.assertIn("route-email-support-team", route_tags)

    def test_outbound_allowlist_prefers_snapshot_email(self) -> None:
        envelope = build_event_envelope(
            {
                "ticket_id": "t-email",
                "order_id": "ord-123",
                "shipping_method": "2 business days",
                "created_at": "2024-12-20T00:00:00Z",
                "message": "Where is my order?",
                "email": "blocked@example.com",
            }
        )
        plan = plan_actions(envelope, safe_mode=False, automation_enabled=True)
        executor = _RecordingExecutor(
            ticket_channel="email",
            ticket_customer_email="allow@example.com",
        )

        with mock.patch.dict(
            os.environ,
            {
                "MW_OUTBOUND_ALLOWLIST_EMAILS": "allow@example.com",
                "RICHPANEL_BOT_AGENT_ID": "agent-123",
            },
            clear=False,
        ):
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
        self.assertTrue(
            any(call["path"].endswith("/send-message") for call in executor.calls)
        )

    def test_outbound_rewrite_hashes_populated(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor()
        rewrite_result = ReplyRewriteResult(
            body="rewritten body",
            rewritten=True,
            reason="applied",
            model="gpt-5.2-chat-latest",
            confidence=0.91,
            dry_run=False,
            fingerprint="fp",
            llm_called=True,
            response_id="resp-1",
        )

        with mock.patch(
            "richpanel_middleware.automation.pipeline.rewrite_reply",
            return_value=rewrite_result,
        ):
            result = execute_order_status_reply(
                envelope,
                plan,
                safe_mode=False,
                automation_enabled=True,
                allow_network=True,
                outbound_enabled=True,
                richpanel_executor=cast(RichpanelExecutor, executor),
            )

        openai_rewrite = result.get("openai_rewrite", {})
        self.assertTrue(openai_rewrite.get("rewritten_changed"))
        self.assertIsNotNone(openai_rewrite.get("original_hash"))
        self.assertIsNotNone(openai_rewrite.get("rewritten_hash"))
        self.assertNotEqual(
            openai_rewrite.get("original_hash"),
            openai_rewrite.get("rewritten_hash"),
        )

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

    def test_outbound_reply_update_failure(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_status="open", reply_status_codes=[500, 500]
        )

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
        self.assertEqual(result["reason"], "reply_update_failed")
        # Expect GET + at least one reply attempt; no tags should be applied.
        self.assertGreaterEqual(len(executor.calls), 2)
        add_tag_calls = [c for c in executor.calls if "/add-tags" in c["path"]]
        self.assertEqual(add_tag_calls, [])

    def test_outbound_exception_includes_openai_rewrite(self) -> None:
        envelope, plan = self._build_order_status_plan()

        class _ExceptionExecutor(_RecordingExecutor):
            def execute(self, method: str, path: str, **kwargs: Any) -> RichpanelResponse:
                if method.upper() == "PUT" and path.startswith("/v1/tickets/"):
                    raise TransportError("simulated write failure")
                return super().execute(method, path, **kwargs)

        executor = _ExceptionExecutor(ticket_status="open")
        rewrite_result = ReplyRewriteResult(
            body="rewritten",
            rewritten=False,
            reason="dry_run",
            model="gpt-5.2-chat-latest",
            confidence=0.0,
            dry_run=True,
            fingerprint="fp",
            llm_called=True,
            response_id=None,
            response_id_unavailable_reason="dry_run",
            error_class="OpenAIDryRun",
        )

        with mock.patch(
            "richpanel_middleware.automation.pipeline.rewrite_reply",
            return_value=rewrite_result,
        ):
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
        self.assertEqual(result["reason"], "exception")
        self.assertIn("openai_rewrite", result)
        self.assertTrue(result["openai_rewrite"]["rewrite_attempted"])

    def test_outbound_reply_dry_run_does_not_send(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_status="open", reply_status_codes=[200, 200], force_dry_run=True
        )

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
        self.assertEqual(result["reason"], "reply_update_failed")
        reply_calls = [
            c
            for c in executor.calls
            if c["method"] == "PUT" and "/v1/tickets/" in c["path"]
        ]
        self.assertGreaterEqual(len(reply_calls), 1)
        for call in reply_calls:
            self.assertTrue(call["kwargs"].get("dry_run", False))

    def test_outbound_retries_do_not_duplicate_comment(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _CommentRetryExecutor()

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
        update_calls = [
            (idx, call)
            for idx, call in enumerate(executor.calls)
            if call["method"] == "PUT"
            and call["path"].startswith("/v1/tickets/")
            and "/add-tags" not in call["path"]
        ]
        self.assertGreaterEqual(len(update_calls), 2)
        first_update_payload = update_calls[0][1]["kwargs"]["json_body"]
        second_update_payload = update_calls[1][1]["kwargs"]["json_body"]
        self.assertTrue(_payload_contains_comment(first_update_payload))
        self.assertFalse(_payload_contains_comment(second_update_payload))

        add_tag_indices = [
            idx
            for idx, call in enumerate(executor.calls)
            if call["method"] == "PUT" and "/add-tags" in call["path"]
        ]
        self.assertTrue(add_tag_indices)
        self.assertGreater(add_tag_indices[0], update_calls[1][0])

    def test_outbound_followup_after_auto_reply_routes_to_email_support(self) -> None:
        envelope, plan = self._build_order_status_plan()
        executor = _RecordingExecutor(
            ticket_status="open", ticket_tags=["mw-auto-replied"]
        )

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
        self.assertEqual(result["reason"], "followup_after_auto_reply")
        self.assertEqual(len(executor.calls), 2)
        self.assertEqual(executor.calls[0]["method"], "GET")
        route_call = executor.calls[1]
        self.assertEqual(route_call["method"], "PUT")
        self.assertIn("/add-tags", route_call["path"])
        route_tags = route_call["kwargs"]["json_body"]["tags"]
        self.assertIsInstance(route_tags, list)
        self.assertEqual(route_tags, sorted(route_tags))
        self.assertIn("route-email-support-team", route_tags)
        self.assertIn("mw-skip-followup-after-auto-reply", route_tags)
        self.assertNotIn("mw-escalated-human", route_tags)

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
        action = [
            action
            for action in plan.actions
            if action.get("type") == "order_status_draft_reply"
        ][0]
        reply_body = action["parameters"].get("draft_reply", {}).get("body", "")

        with self.assertLogs(
            "richpanel_middleware.automation.pipeline", level="INFO"
        ) as captured:
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


def _payload_contains_comment(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("comment"):
        return True
    ticket_payload = payload.get("ticket")
    return isinstance(ticket_payload, dict) and bool(ticket_payload.get("comment"))


class _RecordingExecutor:
    def __init__(
        self,
        *,
        ticket_status: str = "open",
        ticket_tags: list[str] | None = None,
        ticket_channel: str | None = None,
        ticket_customer_email: str | None = None,
        ticket_comments: list[dict[str, Any]] | None = None,
        users: list[dict[str, Any]] | None = None,
        raise_on_get: bool = False,
        reply_status_codes: list[int] | None = None,
        send_message_status_codes: list[int] | None = None,
        force_dry_run: bool = False,
        send_message_operator_flag: bool | None = True,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.ticket_status = ticket_status
        self.ticket_tags = ticket_tags or []
        self.ticket_channel = ticket_channel
        self.ticket_customer_email = ticket_customer_email
        self.ticket_comments = ticket_comments or []
        self.users = users or []
        self.raise_on_get = raise_on_get
        self.reply_status_codes = reply_status_codes or [202]
        self._reply_index = 0
        self.send_message_status_codes = send_message_status_codes or [200]
        self._send_message_index = 0
        self.force_dry_run = force_dry_run
        self.send_message_operator_flag = send_message_operator_flag

    def execute(self, method: str, path: str, **kwargs: Any) -> RichpanelResponse:
        effective_dry_run = self.force_dry_run or kwargs.get("dry_run", False)
        kwargs["dry_run"] = effective_dry_run
        self.calls.append({"method": method, "path": path, "kwargs": kwargs})

        if method.upper() == "GET" and path.startswith("/v1/users"):
            body = json.dumps({"users": self.users}).encode("utf-8")
            return RichpanelResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=body,
                url=path,
                dry_run=kwargs.get("dry_run", False),
            )

        if (
            method.upper() == "GET"
            and path.startswith("/v1/tickets/")
            and "/add-tags" not in path
        ):
            if self.raise_on_get:
                raise TransportError("simulated ticket read failure")
            payload = {"status": self.ticket_status, "tags": self.ticket_tags}
            if self.ticket_channel is not None:
                payload["via"] = {"channel": self.ticket_channel}
            if self.ticket_customer_email is not None:
                via = payload.get("via")
                if not isinstance(via, dict):
                    via = {}
                    payload["via"] = via
                source = via.get("source")
                if not isinstance(source, dict):
                    source = {}
                    via["source"] = source
                source["from"] = {"address": self.ticket_customer_email}
            if self.ticket_comments:
                payload["comments"] = list(self.ticket_comments)
            body = json.dumps(payload).encode("utf-8")
            return RichpanelResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=body,
                url=path,
                dry_run=kwargs.get("dry_run", False),
            )

        if method.upper() == "PUT" and "/add-tags" in path:
            tags = kwargs.get("json_body", {}).get("tags") or []
            self.ticket_tags = sorted(set(self.ticket_tags + tags))

        if method.upper() == "PUT" and path.endswith("/send-message"):
            status_code = (
                self.send_message_status_codes[self._send_message_index]
                if self._send_message_index < len(self.send_message_status_codes)
                else self.send_message_status_codes[-1]
            )
            self._send_message_index += 1
            if not effective_dry_run and 200 <= status_code < 300:
                if self.send_message_operator_flag is not None:
                    self.ticket_comments.append(
                        {
                            "is_operator": self.send_message_operator_flag,
                            "source": "middleware",
                        }
                    )
            return RichpanelResponse(
                status_code=status_code,
                headers={},
                body=b"",
                url=path,
                dry_run=effective_dry_run,
            )

        if method.upper() == "PUT" and path.startswith("/v1/tickets/"):
            payload = kwargs.get("json_body") or {}
            ticket_payload = payload.get("ticket") or {}
            status = ticket_payload.get("status") or payload.get("status")
            state = ticket_payload.get("state") or payload.get("state")
            if status:
                self.ticket_status = str(status).lower()
            if state:
                self.ticket_status = str(state).lower()

        status_code = (
            self.reply_status_codes[self._reply_index]
            if self._reply_index < len(self.reply_status_codes)
            else self.reply_status_codes[-1]
        )
        self._reply_index += 1

        return RichpanelResponse(
            status_code=status_code,
            headers={},
            body=b"",
            url=path,
            dry_run=effective_dry_run,
        )


class _CommentRetryExecutor:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.ticket_status = "open"
        self.ticket_tags: list[str] = []
        self.reply_status_codes = [202, 202]
        self._reply_index = 0
        self._update_calls = 0

    def execute(self, method: str, path: str, **kwargs: Any) -> RichpanelResponse:
        effective_dry_run = kwargs.get("dry_run", False)
        kwargs["dry_run"] = effective_dry_run
        self.calls.append({"method": method, "path": path, "kwargs": kwargs})

        if method.upper() == "GET" and path.startswith("/v1/tickets/"):
            body = json.dumps(
                {"status": self.ticket_status, "tags": self.ticket_tags}
            ).encode("utf-8")
            return RichpanelResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=body,
                url=path,
                dry_run=effective_dry_run,
            )

        if method.upper() == "PUT" and "/add-tags" in path:
            tags = kwargs.get("json_body", {}).get("tags") or []
            self.ticket_tags = sorted(set(self.ticket_tags + tags))
            return RichpanelResponse(
                status_code=200,
                headers={},
                body=b"",
                url=path,
                dry_run=effective_dry_run,
            )

        if method.upper() == "PUT" and path.startswith("/v1/tickets/"):
            status_code = (
                self.reply_status_codes[self._reply_index]
                if self._reply_index < len(self.reply_status_codes)
                else self.reply_status_codes[-1]
            )
            self._reply_index += 1
            if self._update_calls >= 1:
                payload = kwargs.get("json_body") or {}
                ticket_payload = payload.get("ticket") or {}
                status = ticket_payload.get("status") or payload.get("status")
                state = ticket_payload.get("state") or payload.get("state")
                if status:
                    self.ticket_status = str(status).lower()
                if state:
                    self.ticket_status = str(state).lower()
            self._update_calls += 1
            return RichpanelResponse(
                status_code=status_code,
                headers={},
                body=b"",
                url=path,
                dry_run=effective_dry_run,
            )

        return RichpanelResponse(
            status_code=500,
            headers={},
            body=b"",
            url=path,
            dry_run=effective_dry_run,
        )


class BotAgentResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("RICHPANEL_BOT_AGENT_ID", None)

    def test_resolve_bot_agent_id_prefers_env(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"RICHPANEL_BOT_AGENT_ID": "agent-xyz"},
            clear=False,
        ):
            agent_id, source = _resolve_bot_agent_id(
                env_name="dev", allow_network=True
            )
        self.assertEqual(agent_id, "agent-xyz")
        self.assertEqual(source, "env")

    def test_resolve_bot_agent_id_network_disabled(self) -> None:
        agent_id, source = _resolve_bot_agent_id(env_name="dev", allow_network=False)
        self.assertIsNone(agent_id)
        self.assertEqual(source, "missing")

    def test_resolve_bot_agent_id_from_secrets(self) -> None:
        with mock.patch(
            "richpanel_middleware.automation.pipeline._load_secret_value",
            return_value='{"bot_agent_id": "agent-123"}',
        ):
            agent_id, source = _resolve_bot_agent_id(
                env_name="dev", allow_network=True
            )
        self.assertEqual(agent_id, "agent-123")
        self.assertEqual(source, "secrets_manager")

    def test_extract_bot_agent_id_plain(self) -> None:
        self.assertEqual(_extract_bot_agent_id("agent-xyz"), "agent-xyz")

    def test_extract_bot_agent_id_unknown_json(self) -> None:
        self.assertIsNone(_extract_bot_agent_id("{\"other_key\": \"value\"}"))

    def test_extract_bot_agent_id_numeric(self) -> None:
        self.assertEqual(_extract_bot_agent_id("12345"), "12345")
        self.assertEqual(_extract_bot_agent_id("{\"bot_agent_id\": 12345}"), "12345")


class BotAgentSecretLoadTests(unittest.TestCase):
    def test_load_secret_value_boto3_missing(self) -> None:
        with mock.patch.object(pipeline_module, "boto3", None):
            self.assertIsNone(_load_secret_value("secret-id"))

    def test_load_secret_value_secret_string(self) -> None:
        class _Client:
            def get_secret_value(self, SecretId: str) -> dict:
                return {"SecretString": "secret-value"}

        class _Boto3:
            def client(self, name: str):
                self.last_client = name
                return _Client()

        with mock.patch.object(pipeline_module, "boto3", _Boto3()):
            self.assertEqual(_load_secret_value("secret-id"), "secret-value")

    def test_load_secret_value_secret_binary(self) -> None:
        class _Client:
            def get_secret_value(self, SecretId: str) -> dict:
                return {"SecretBinary": b"secret-binary"}

        class _Boto3:
            def client(self, name: str):
                return _Client()

        with mock.patch.object(pipeline_module, "boto3", _Boto3()):
            self.assertEqual(_load_secret_value("secret-id"), "secret-binary")

    def test_load_secret_value_cache_hit(self) -> None:
        _SECRET_VALUE_CACHE.clear()
        _SECRET_VALUE_CACHE["secret-id"] = {
            "value": "cached-value",
            "expires_at": time.time() + _SECRET_VALUE_CACHE_TTL_SECONDS,
        }
        with mock.patch.object(pipeline_module, "boto3", None):
            self.assertEqual(_load_secret_value("secret-id"), "cached-value")


class ReadOnlyGuardTests(unittest.TestCase):
    def test_read_only_guard_env_override(self) -> None:
        with mock.patch.dict(os.environ, {"RICHPANEL_READ_ONLY": "true"}):
            self.assertTrue(_read_only_guard_active("dev"))

    def test_read_only_guard_write_disabled(self) -> None:
        with mock.patch.dict(os.environ, {"RICHPANEL_WRITE_DISABLED": "true"}):
            self.assertTrue(_read_only_guard_active("dev"))

    def test_read_only_guard_prod_env(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(_read_only_guard_active("prod"))

    def test_read_only_guard_false_in_dev(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_read_only_guard_active("dev"))

    def test_read_only_guard_false_override_in_prod(self) -> None:
        with mock.patch.dict(os.environ, {"RICHPANEL_READ_ONLY": "false"}):
            self.assertFalse(_read_only_guard_active("prod"))

    def test_safe_ticket_snapshot_fetch_channel_fallback(self) -> None:
        class _ChannelExecutor:
            def execute(self, method: str, path: str, **kwargs: Any) -> RichpanelResponse:
                body = json.dumps(
                    {"channel": "Email", "status": "open", "tags": []}
                ).encode("utf-8")
                return RichpanelResponse(
                    status_code=200,
                    headers={"content-type": "application/json"},
                    body=body,
                    url=path,
                    dry_run=kwargs.get("dry_run", False),
                )

        metadata, channel, customer_email = _safe_ticket_snapshot_fetch(
            "ticket-1",
            executor=cast(RichpanelExecutor, _ChannelExecutor()),
            allow_network=True,
        )
        self.assertIsNotNone(metadata)
        self.assertEqual(channel, "email")
        self.assertIsNone(customer_email)


class OutboundAllowlistTests(unittest.TestCase):
    def test_allowlist_exact_email_match_case_insensitive(self) -> None:
        allowlist_emails = _parse_allowlist_entries("Test@Example.com")
        allowed, reason = _match_allowlist_email(
            "test@example.com",
            allowlist_emails=allowlist_emails,
            allowlist_domains=set(),
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "email_match")

    def test_allowlist_domain_match_case_insensitive(self) -> None:
        allowlist_domains = _parse_allowlist_entries("Example.COM", strip_at=True)
        allowed, reason = _match_allowlist_email(
            "user@example.com",
            allowlist_emails=set(),
            allowlist_domains=allowlist_domains,
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "domain_match")

    def test_allowlist_whitespace_trimming(self) -> None:
        allowlist_emails = _parse_allowlist_entries("  user@example.com ,  ")
        allowlist_domains = _parse_allowlist_entries("  Example.com  ", strip_at=True)
        email_allowed, _ = _match_allowlist_email(
            "USER@example.com",
            allowlist_emails=allowlist_emails,
            allowlist_domains=set(),
        )
        domain_allowed, _ = _match_allowlist_email(
            "other@example.com",
            allowlist_emails=set(),
            allowlist_domains=allowlist_domains,
        )
        self.assertTrue(email_allowed)
        self.assertTrue(domain_allowed)

    def test_allowlist_domain_strips_at_prefix(self) -> None:
        allowlist_domains = _parse_allowlist_entries("@Example.com", strip_at=True)
        allowed, reason = _match_allowlist_email(
            "user@example.com",
            allowlist_emails=set(),
            allowlist_domains=allowlist_domains,
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "domain_match")

    def test_allowlist_empty_denies(self) -> None:
        allowed, reason = _match_allowlist_email(
            "user@example.com",
            allowlist_emails=set(),
            allowlist_domains=set(),
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "allowlist_empty")

    def test_allowlist_missing_email_denies(self) -> None:
        allowed, reason = _match_allowlist_email(
            None,
            allowlist_emails={"user@example.com"},
            allowlist_domains={"example.com"},
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "missing_email")

    def test_allowlist_not_allowlisted_denies(self) -> None:
        allowed, reason = _match_allowlist_email(
            "user@other.com",
            allowlist_emails={"allow@example.com"},
            allowlist_domains={"example.com"},
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "not_allowlisted")


class CustomerEmailExtractionTests(unittest.TestCase):
    def test_extract_customer_email_from_via_source(self) -> None:
        payload = {"via": {"source": {"from": {"address": "User@Example.com"}}}}
        self.assertEqual(
            _extract_customer_email_from_payload(payload), "user@example.com"
        )

    def test_extract_customer_email_from_via_from_string(self) -> None:
        payload = {"via": {"from": "User@Example.com"}}
        self.assertEqual(
            _extract_customer_email_from_payload(payload), "user@example.com"
        )

    def test_extract_customer_email_from_customer_profile(self) -> None:
        payload = {"customer_profile": {"email": "Person@Example.com"}}
        self.assertEqual(
            _extract_customer_email_from_payload(payload), "person@example.com"
        )

    def test_extract_customer_email_from_sender(self) -> None:
        payload = {"sender": {"address": "Sender@Example.com"}}
        self.assertEqual(
            _extract_customer_email_from_payload(payload), "sender@example.com"
        )

    def test_extract_customer_email_returns_none_when_missing(self) -> None:
        self.assertIsNone(_extract_customer_email_from_payload({"foo": "bar"}))


class OutboundRoutingTagsTests(unittest.TestCase):
    def setUp(self) -> None:
        worker.boto3 = None  # type: ignore
        worker._FLAG_CACHE.update(
            {"safe_mode": True, "automation_enabled": False, "expires_at": 0.0}
        )
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


def _build_suite() -> unittest.TestSuite:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FingerprintReplyBodyTests)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(PipelineTests))
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(OutboundOrderStatusTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(BotAgentResolutionTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(BotAgentSecretLoadTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReadOnlyGuardTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(OutboundAllowlistTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(CustomerEmailExtractionTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(OutboundRoutingTagsTests)
    )
    backend_tests = ROOT / "backend" / "tests"
    if backend_tests.exists():
        suite.addTests(
            unittest.defaultTestLoader.discover(
                str(backend_tests), pattern="test_*.py", top_level_dir=str(ROOT)
            )
        )
    return suite


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    return _build_suite()


def main() -> int:  # pragma: no cover
    suite = _build_suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
