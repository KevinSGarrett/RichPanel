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
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dev_e2e_smoke import (  # type: ignore  # noqa: E402
    _check_pii_safe,
    _classify_order_status_result,
    _compute_middleware_outcome,
    _compute_reply_evidence,
    _business_day_anchor,
    _build_followup_payload,
    _prepare_followup_proof,
    append_summary,
    _redact_command,
    _iso_business_days_before,
    _order_status_no_tracking_payload,
    _order_status_no_tracking_short_window_payload,
    _apply_fallback_close,
    _diagnose_ticket_update,
    _sanitize_decimals,
    _sanitize_response_metadata,
    _sanitize_ts_action_id,
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
    seeded_order_id = (
        conversation_id or f"DEV-ORDER-{_fingerprint(order_seed, length=8).upper()}"
    )
    tracking_number = (
        f"TRACK-{_fingerprint(seeded_order_id + order_seed, length=10).upper()}"
    )
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
        payload = _order_status_scenario_payload(
            "TEST_RUN", conversation_id="test-conv-123"
        )

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

        serialized = json.dumps(payload)
        self.assertNotIn("@", serialized)
        self.assertNotIn("%40", serialized)
        self.assertNotIn("mail.", serialized)

    def test_order_status_no_tracking_shape(self) -> None:
        payload = _order_status_no_tracking_payload(
            "RUN_NT", conversation_id="conv-no-track-1"
        )

        self.assertEqual(payload["scenario"], "order_status_no_tracking")
        self.assertEqual(payload["intent"], "order_status_tracking")
        self.assertIn("shipping_method", payload)
        self.assertIn("order_created_at", payload)
        self.assertIsNone(payload.get("tracking_number"))
        self.assertIsNone(payload.get("tracking_url"))
        self.assertEqual(payload["tracking"]["status"], "label_pending")

    def test_order_status_no_tracking_short_window_shape(self) -> None:
        payload = _order_status_no_tracking_short_window_payload(
            "RUN_NT_SHORT", conversation_id="conv-no-track-short-1"
        )

        self.assertEqual(
            payload["scenario"], "order_status_no_tracking_short_window"
        )
        self.assertEqual(payload["intent"], "order_status_tracking")
        self.assertIn("shipping_method", payload)
        self.assertIsNone(payload.get("tracking_number"))
        self.assertIsNone(payload.get("tracking_url"))
        self.assertIn("standard (3-5 business days)", payload["shipping_method"].lower())

        order_date = datetime.fromisoformat(payload["order_created_at"])
        ticket_date = datetime.fromisoformat(payload["ticket_created_at"])
        business_days = 0
        cursor = order_date
        while cursor < ticket_date:
            cursor += timedelta(days=1)
            if cursor.weekday() < 5:
                business_days += 1
        self.assertEqual(business_days, 2)

    def test_business_day_anchor_skips_weekend(self) -> None:
        saturday = datetime(2024, 1, 6, 12, tzinfo=timezone.utc)
        monday = _business_day_anchor(saturday)

        self.assertEqual(monday.weekday(), 0)
        self.assertEqual(monday.date(), datetime(2024, 1, 8, tzinfo=timezone.utc).date())

    def test_iso_business_days_before_validation(self) -> None:
        anchor = datetime(2024, 1, 8, 12, tzinfo=timezone.utc)
        before_two = _iso_business_days_before(anchor, 2)

        self.assertTrue(before_two.startswith("2024-01-04"))
        with self.assertRaises(ValueError):
            _iso_business_days_before(anchor, -1)


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
            self.calls.append(
                {"method": method, "path": path, "body": json_body, "dry_run": dry_run}
            )
            return DiagnosticsTests._MockResponse(self.status_code, dry_run, path)

    def test_diagnose_skips_without_confirm(self) -> None:
        executor = self._MockExecutor()
        result = _diagnose_ticket_update(
            executor,  # type: ignore[arg-type]
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
            executor,  # type: ignore[arg-type]
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
        sanitized = _sanitize_response_metadata(
            self._MockResponse(200, False, "/v1/tickets/abc")
        )
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


class ClassificationTests(unittest.TestCase):
    def test_pass_strong_requires_success_tag(self) -> None:
        strong, reason = _classify_order_status_result(
            base_pass=True,
            status_resolved_ok=True,
            middleware_tag_ok=True,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=False,
            failed=[],
        )
        self.assertEqual(strong, "PASS_STRONG")
        self.assertIsNone(reason)

        weak, weak_reason = _classify_order_status_result(
            base_pass=True,
            status_resolved_ok=True,
            middleware_tag_ok=False,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=False,
            failed=[],
        )
        self.assertEqual(weak, "PASS_WEAK")
        self.assertEqual(weak_reason, "status_or_success_tag_missing")

    def test_skip_tags_fail(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=True,
            status_resolved_ok=True,
            middleware_tag_ok=True,
            middleware_ok=True,
            skip_tags_present_ok=False,
            auto_close_applied=False,
            fallback_used=False,
            failed=["no_skip_tags"],
        )
        self.assertEqual(result, "FAIL")
        self.assertEqual(reason, "skip_or_escalation_tags_present")

    def test_fallback_used_marks_pass_weak(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=True,
            status_resolved_ok=False,
            middleware_tag_ok=False,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=True,
            failed=[],
        )
        self.assertEqual(result, "PASS_WEAK")
        self.assertEqual(reason, "fallback_close_used_by_harness")

    def test_fallback_used_with_failed_criteria_marks_fail_debug(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=False,
            status_resolved_ok=False,
            middleware_tag_ok=False,
            middleware_ok=False,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=True,
            failed=["status_resolved_or_closed"],
        )
        self.assertEqual(result, "FAIL_DEBUG")
        self.assertEqual(reason, "fallback_close_used_but_criteria_failed")

    def test_fail_when_base_pass_false(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=False,
            status_resolved_ok=True,
            middleware_tag_ok=True,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=False,
            failed=["middleware_outcome"],
        )
        self.assertEqual(result, "FAIL")
        self.assertEqual(reason, "Failed criteria: middleware_outcome")

    def test_auto_close_applied_degrades_to_pass_weak(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=True,
            status_resolved_ok=True,
            middleware_tag_ok=True,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=True,
            fallback_used=False,
            failed=[],
        )
        self.assertEqual(result, "PASS_WEAK")
        self.assertEqual(reason, "debug_auto_close_applied")

    def test_auto_close_fail_debug_when_criteria_missing(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=False,
            status_resolved_ok=False,
            middleware_tag_ok=False,
            middleware_ok=False,
            skip_tags_present_ok=True,
            auto_close_applied=True,
            fallback_used=False,
            failed=["status_resolved_or_closed"],
        )
        self.assertEqual(result, "FAIL_DEBUG")
        self.assertEqual(reason, "debug_auto_close_applied_but_criteria_failed")


class PIISafetyTests(unittest.TestCase):
    def test_pii_scan_detects_email(self) -> None:
        self.assertIsNotNone(_check_pii_safe('{"email":"user@example.com"}'))
        self.assertIsNotNone(_check_pii_safe('{"encoded":"foo%40bar.com"}'))

    def test_pii_scan_detects_event_identifier(self) -> None:
        self.assertIsNotNone(_check_pii_safe('{"event_id":"evt:abc123"}'))

    def test_pii_scan_detects_ticket_number_flag(self) -> None:
        payload = '{"command":"python scripts/dev_e2e_smoke.py --ticket-number 1040"}'
        self.assertIsNotNone(_check_pii_safe(payload))

    def test_redact_command_masks_sensitive_flags(self) -> None:
        cmd = _redact_command(
            [
                "scripts/dev_e2e_smoke.py",
                "--ticket-number",
                "1039",
                "--event-id",
                "evt:ac89d31a",
                "--scenario",
                "order_status",
            ]
        )
        self.assertIn("--ticket-number <redacted>", cmd)
        self.assertIn("--event-id <redacted>", cmd)
        self.assertNotIn("1039", cmd)
        self.assertNotIn("evt:ac89d31a", cmd)
        self.assertTrue(cmd.startswith("python "))

    def test_sanitize_ts_action_id_fingerprints_event(self) -> None:
        original = "2026-01-17T00:00:00Z#evt:abc12345"
        sanitized = _sanitize_ts_action_id(original)
        self.assertEqual(
            sanitized,
            f"2026-01-17T00:00:00Z#fingerprint:{_fingerprint('evt:abc12345')}",
        )


class FollowupProofTests(unittest.TestCase):
    def test_followup_payload_inherits_parent_and_sets_followup_fields(self) -> None:
        base = {
            "event_id": "evt:primary:1234",
            "scenario_name": "order_status",
            "customer_message": "orig",
        }
        followup = _build_followup_payload(
            base_payload=base,
            followup_message="follow-up ping",
            scenario_variant="order_status_tracking",
        )

        self.assertNotEqual(followup["event_id"], base["event_id"])
        self.assertTrue(followup["event_id"].startswith("evt:followup:"))
        self.assertEqual(followup["parent_event_id"], base["event_id"])
        self.assertTrue(followup["followup"])
        self.assertEqual(followup["customer_message"], "follow-up ping")
        self.assertEqual(followup["scenario"], "order_status_tracking_followup")
        self.assertEqual(followup["scenario_name"], "order_status_followup")
        self.assertIn("message_id", followup)
        self.assertIn("nonce", followup)

    def test_followup_fingerprint_populated_when_performed(self) -> None:
        followup_event_id = "evt:followup:abc12345"
        followup_item = {"status": "performed", "mode": "safe"}
        fingerprint, proof = _prepare_followup_proof(
            followup_event_id=followup_event_id,
            followup_item=followup_item,
            followup_tags_added=["mw-reply-sent"],
            followup_tags_removed=[],
            followup_skip_tags_added=[],
            followup_middleware_tags=["mw-reply-sent"],
            followup_status_after="resolved",
            followup_message_count_delta=1,
            followup_updated_at_delta=2.5,
            followup_reply_sent=True,
            followup_reply_reason="auto_reply_sent",
            followup_routed_support=False,
        )

        self.assertEqual(fingerprint, _fingerprint(followup_event_id))
        self.assertTrue(proof["performed"])
        self.assertEqual(proof["event_id_fingerprint"], fingerprint)
        self.assertEqual(
            proof["idempotency_record"], {"status": "performed", "mode": "safe"}
        )
        self.assertEqual(proof["message_count_delta"], 1)
        self.assertEqual(proof["updated_at_delta_seconds"], 2.5)
        self.assertTrue(proof["reply_sent"])
        self.assertEqual(proof["reply_reason"], "auto_reply_sent")

    def test_followup_proof_handles_missing_event(self) -> None:
        fingerprint, proof = _prepare_followup_proof(
            followup_event_id=None,
            followup_item=None,
            followup_tags_added=[],
            followup_tags_removed=[],
            followup_skip_tags_added=[],
            followup_middleware_tags=[],
            followup_status_after=None,
            followup_message_count_delta=None,
            followup_updated_at_delta=None,
            followup_reply_sent=None,
            followup_reply_reason=None,
            followup_routed_support=None,
        )

        self.assertIsNone(fingerprint)
        self.assertFalse(proof["performed"])
        self.assertIsNone(proof["event_id_fingerprint"])
        self.assertIsNone(proof["idempotency_record"])
        self.assertIsNone(proof["status_after"])
        self.assertIsNone(proof["reply_sent"])


class SummaryAppendTests(unittest.TestCase):
    def test_append_summary_writes_expected_sections(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "summary.md"
            data = {
                "event_id_fingerprint": "fingerprint:abc123",
                "endpoint": "https://example.com",
                "queue_url": "https://sqs.example.com/queue",
                "ddb_table": "ddb-table",
                "ddb_console_url": "https://console.aws.amazon.com/ddb",
                "routing_category": "order_status",
                "routing_tags": ["mw-routing", "mw-auto"],
                "draft_action_present": True,
                "draft_reply_count": 1,
                "draft_replies_safe": [
                    {"reason": "test", "prompt_fingerprint": "pfp", "dry_run": True}
                ],
                "logs_group": "/aws/lambda/rp-mw-dev-worker",
                "logs_console_url": "https://console.aws.amazon.com/cloudwatch",
                "idempotency_mode": "applied",
                "idempotency_status": "observed",
                "conversation_state_table": "state-table",
                "conversation_state_console": "https://console.aws.amazon.com/state",
                "audit_trail_table": "audit-table",
                "audit_console": "https://console.aws.amazon.com/audit",
                "conversation_id": "conv-123",
                "audit_sort_key": "ts#123",
                "dashboard_name": "rp-mw-dev-ops",
                "alarm_names": ["alarm-one", "alarm-two"],
            }

            append_summary(str(path), env_name="dev", data=data)

            content = path.read_text(encoding="utf-8")
            self.assertIn("## Dev E2E Smoke", content)
            self.assertIn("fingerprint:abc123", content)
            self.assertIn("CloudWatch alarms: `alarm-one`, `alarm-two`", content)
            self.assertIn("Draft replies (safe fields)", content)
            self.assertIn("audit-table", content)


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

        def execute(
            self, method: str, path: str, **kwargs: Any
        ) -> "FallbackCloseTests._Resp":
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
            ticket_executor=execu,  # type: ignore[arg-type]
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
        execute_routing_tags(
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
        path_arg = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("path")
        )

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

        execute_routing_tags(
            envelope,
            plan,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            richpanel_executor=mock_executor,
        )

        call_args = mock_executor.execute.call_args
        path_arg = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("path")
        )

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
