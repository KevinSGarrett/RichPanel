#!/usr/bin/env python3
"""
test_e2e_smoke_encoding.py

Unit tests for E2E smoke script URL encoding and scenario payload handling.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(SRC))
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dev_e2e_smoke import (  # type: ignore  # noqa: E402
    SmokeFailure,
    ClientError,
    _check_pii_safe,
    _classify_order_status_result,
    _compute_middleware_outcome,
    _compute_reply_evidence,
    _compute_draft_reply_body,
    _compute_operator_reply_metrics,
    _business_day_anchor,
    _build_followup_payload,
    _prepare_followup_proof,
    _extract_latest_comment_body,
    _resolve_requirement_flags,
    _extract_openai_routing_evidence,
    _extract_openai_rewrite_evidence,
    _extract_order_status_intent_evidence,
    _evaluate_outbound_evidence,
    _evaluate_outbound_attempted,
    _classify_outbound_failure,
    _evaluate_send_message_status,
    _evaluate_operator_reply_evidence,
    _evaluate_send_message_evidence,
    _evaluate_allowlist_blocked_evidence,
    _evaluate_support_routing,
    _evaluate_order_match_evidence,
    _order_resolution_is_order_number,
    _extract_order_match_method,
    _extract_order_resolution_from_actions,
    _normalize_optional_text,
    _probe_order_resolution_from_ticket,
    _detect_order_match_by_number,
    _should_skip_allowlist_blocked,
    _unexpected_outbound_blocked,
    _evaluate_openai_requirements,
    _build_operator_send_message_proof_fields,
    _build_operator_send_message_richpanel_fields,
    _build_operator_send_message_criteria,
    _append_operator_send_message_criteria_details,
    _resolve_outbound_endpoint_used,
    _fetch_ticket_snapshot,
    _fetch_latest_reply_body,
    _fetch_latest_reply_hash,
    _reply_contains_tracking_url,
    _reply_contains_tracking_number_like,
    _reply_contains_eta_date_like,
    _collect_reply_body_candidates,
    _evaluate_reply_content_flags,
    append_summary,
    _redact_command,
    _redact_path,
    _extract_endpoint_variant,
    _sanitize_ticket_snapshot,
    _sanitize_tag_result,
    _iso_business_days_before,
    _order_status_no_tracking_payload,
    _order_status_no_tracking_short_window_payload,
    _order_status_no_tracking_standard_shipping_3_5_payload,
    _order_status_tracking_standard_shipping_payload,
    _not_order_status_payload,
    _order_status_no_match_payload,
    _order_status_fallback_email_payload,
    _seed_order_id,
    _seed_order_number,
    _build_skip_proof_payload,
    _write_proof_payload,
    _apply_fallback_close,
    _build_create_ticket_payload,
    _diagnose_ticket_update,
    _extract_created_ticket_fields,
    _create_sandbox_email_ticket,
    _redact_identifier,
    _resolve_smoke_ticket_text,
    _resolve_order_number,
    _fetch_recent_shopify_order_number,
    _SMOKE_TICKET_TAGS,
    _parse_allowlist_entries,
    _fetch_lambda_allowlist_config,
    _to_bool,
    _sanitize_decimals,
    _sanitize_response_metadata,
    _sanitize_ts_action_id,
    _wait_for_ticket_ready,
    _wait_for_ticket_tags,
    _extract_outbound_result,
    _send_message_used_from_outbound_result,
    _send_message_status_from_outbound_result,
    _resolve_send_message_used,
    _resolve_send_message_status_code,
    _resolve_operator_reply_reason,
    wait_for_openai_rewrite_state_record,
    wait_for_openai_rewrite_audit_record,
    build_payload,
    parse_args,
    validate_routing,
)
from create_sandbox_email_ticket import (  # type: ignore  # noqa: E402
    _require_prod_write_ack as _require_prod_write_ack_script,
)
from create_sandbox_chat_ticket import (  # type: ignore  # noqa: E402
    _build_ticket_payload as _build_chat_ticket_payload,
    _redact_emails as _chat_redact_emails,
    _extract_ticket_fields as _extract_chat_ticket_fields,
    _require_prod_write_ack as _require_prod_write_ack_chat,
    main as _chat_ticket_main,
)

from richpanel_middleware.integrations.richpanel.client import (  # type: ignore  # noqa: E402
    RichpanelRequestError,
    RichpanelResponse,
    RichpanelWriteDisabledError,
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
        shipping_method = payload["shipping_method"].lower()
        self.assertIn("standard shipping", shipping_method)
        self.assertFalse(any(char.isdigit() for char in shipping_method))

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
        shipping_method = payload["shipping_method"].lower()
        self.assertIn("standard shipping", shipping_method)
        self.assertFalse(any(char.isdigit() for char in shipping_method))

        order_date = datetime.fromisoformat(payload["order_created_at"])
        ticket_date = datetime.fromisoformat(payload["ticket_created_at"])
        business_days = 0
        cursor = order_date
        while cursor < ticket_date:
            cursor += timedelta(days=1)
            if cursor.weekday() < 5:
                business_days += 1
        self.assertEqual(business_days, 2)

    def test_order_status_no_tracking_standard_shipping_3_5_shape(self) -> None:
        payload = _order_status_no_tracking_standard_shipping_3_5_payload(
            "RUN_JOHN", conversation_id="conv-no-track-john-1"
        )

        self.assertEqual(
            payload["scenario"], "order_status_no_tracking_standard_shipping_3_5"
        )
        self.assertEqual(payload["intent"], "order_status_tracking")
        self.assertIsNone(payload.get("tracking_number"))
        self.assertIsNone(payload.get("tracking_url"))
        shipping_method = payload["shipping_method"].lower()
        self.assertIn("standard shipping", shipping_method)
        self.assertFalse(any(char.isdigit() for char in shipping_method))

        order_date = datetime.fromisoformat(payload["order_created_at"])
        ticket_date = datetime.fromisoformat(payload["ticket_created_at"])
        self.assertEqual(order_date.weekday(), 0)
        self.assertEqual(ticket_date.weekday(), 2)
        self.assertLessEqual(order_date, ticket_date)
        business_days = 0
        cursor = order_date
        while cursor < ticket_date:
            cursor += timedelta(days=1)
            if cursor.weekday() < 5:
                business_days += 1
        self.assertEqual(business_days, 2)

    def test_order_status_tracking_standard_shipping_shape(self) -> None:
        payload = _order_status_tracking_standard_shipping_payload(
            "RUN_TRACK", conversation_id="conv-track-1"
        )

        self.assertEqual(
            payload["scenario"], "order_status_tracking_standard_shipping"
        )
        self.assertEqual(payload["intent"], "order_status_tracking")
        self.assertEqual(payload["tracking_number"], "1Z999AA10123456784")
        self.assertEqual(
            payload["tracking_url"],
            "https://www.ups.com/track?loc=en_US&tracknum=1Z999AA10123456784",
        )
        self.assertEqual(payload["shipping_method"], "Standard Shipping")
        order_date = datetime.fromisoformat(payload["order_created_at"])
        ticket_date = datetime.fromisoformat(payload["ticket_created_at"])
        self.assertEqual(
            order_date.date(),
            datetime(2026, 2, 2, tzinfo=timezone.utc).date(),
        )
        self.assertEqual(
            ticket_date.date(),
            datetime(2026, 2, 4, tzinfo=timezone.utc).date(),
        )
        self.assertEqual(payload["tracking"]["status_url"], payload["tracking_url"])

    def test_not_order_status_payload_shape(self) -> None:
        payload = _not_order_status_payload("RUN_NOT_OS", conversation_id="conv-123")
        self.assertEqual(payload["scenario"], "not_order_status")
        self.assertIn("cancel", payload["customer_message"].lower())
        self.assertNotIn("tracking_number", payload)
        self.assertNotIn("order_id", payload)
        serialized = json.dumps(payload)
        self.assertNotIn("@", serialized)

    def test_order_status_fallback_email_payload_shape(self) -> None:
        payload = _order_status_fallback_email_payload(
            "RUN_FALLBACK", conversation_id="conv-fallback"
        )
        self.assertEqual(payload["scenario"], "order_status_fallback_email_match")
        self.assertEqual(payload["intent"], "order_status_tracking")
        self.assertIn("customer_message", payload)
        self.assertIn("ticket_created_at", payload)
        self.assertIn("customer_profile", payload)
        self.assertNotIn("order_number", payload)

    def test_order_status_no_match_payload_shape(self) -> None:
        payload = _order_status_no_match_payload(
            "RUN_NO_MATCH", conversation_id="conv-456"
        )
        self.assertEqual(payload["scenario"], "order_status_no_match")
        self.assertTrue(payload["order_number"].startswith("FAKE-"))
        self.assertNotIn("tracking_number", payload)
        serialized = json.dumps(payload)
        self.assertNotIn("@", serialized)

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


class DraftReplyHelperTests(unittest.TestCase):
    def test_compute_draft_reply_body_with_tracking(self) -> None:
        payload: dict[str, Any] = {
            "order": {
                "order_id": "ORDER-1",
                "created_at": "2026-01-05T10:00:00+00:00",
                "shipping_method": "Standard Shipping",
                "tracking_number": "TRACK-123",
                "tracking_url": "https://tracking.example.com/track/TRACK-123",
                "carrier": "UPS",
            },
            "ticket_created_at": "2026-01-07T10:00:00+00:00",
        }
        inquiry_date = cast(str, payload["ticket_created_at"])
        body = _compute_draft_reply_body(
            payload,
            delivery_estimate=None,
            inquiry_date=inquiry_date,
        )
        self.assertIsInstance(body, str)
        body = cast(str, body)
        self.assertIn("tracking information", body.lower())

    def test_compute_draft_reply_body_no_tracking_uses_estimate(self) -> None:
        from richpanel_middleware.automation.delivery_estimate import (
            compute_delivery_estimate,
        )

        payload: dict[str, Any] = {
            "order": {
                "order_id": "ORDER-2",
                "created_at": "2026-01-05T10:00:00+00:00",
                "shipping_method": "Standard Shipping",
            },
            "ticket_created_at": "2026-01-07T10:00:00+00:00",
        }
        order = cast(dict[str, Any], payload["order"])
        inquiry_date = cast(str, payload["ticket_created_at"])
        estimate = compute_delivery_estimate(
            cast(str, order["created_at"]),
            cast(str, order["shipping_method"]),
            inquiry_date,
        )
        body = _compute_draft_reply_body(
            payload,
            delivery_estimate=estimate,
            inquiry_date=inquiry_date,
        )
        self.assertIsInstance(body, str)
        body = cast(str, body)
        self.assertIn("standard (3-5 business days)", body.lower())
        self.assertIn("1-3 business days", body.lower())

    def test_extract_latest_comment_body_prefers_operator(self) -> None:
        comments = [
            {"plain_body": "customer note", "is_operator": False},
            {"plain_body": "agent reply", "is_operator": True},
        ]
        body = _extract_latest_comment_body(comments)
        self.assertEqual(body, "agent reply")

    def test_extract_latest_comment_body_prefers_middleware_source(self) -> None:
        comments = [
            {"plain_body": "agent reply", "is_operator": True, "source": "agent"},
            {
                "plain_body": "middleware reply",
                "is_operator": True,
                "source": "middleware",
            },
        ]
        body = _extract_latest_comment_body(comments)
        self.assertEqual(body, "middleware reply")

    def test_extract_latest_comment_body_fallback(self) -> None:
        comments = [
            {"plain_body": "first", "is_operator": False},
            {"body": "second", "is_operator": False},
        ]
        body = _extract_latest_comment_body(comments)
        self.assertIsNone(body)

    def test_fetch_latest_reply_hash(self) -> None:
        comments = [
            {"plain_body": "customer note", "is_operator": False},
            {"plain_body": "agent reply", "is_operator": True},
        ]

        class _Resp:
            def json(self) -> dict:
                return {"ticket": {"comments": comments}}

        class _Exec:
            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp()

        executor = _Exec()
        expected = _fingerprint("agent reply")
        result = _fetch_latest_reply_hash(
            cast(Any, executor),
            "ticket-123",
            allow_network=True,
        )
        self.assertEqual(result, expected)

    def test_fetch_latest_reply_hash_no_network(self) -> None:
        executor = MagicMock()
        result = _fetch_latest_reply_hash(
            cast(Any, executor),
            "ticket-123",
            allow_network=False,
        )
        self.assertIsNone(result)
        executor.execute.assert_not_called()


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
        self.assertEqual(self._MockResponse(200, False, "/v1/tickets").json(), {})
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

    def test_reply_evidence_middleware_source_requires_delta(self) -> None:
        evidence, reason = _compute_reply_evidence(
            status_changed=False,
            updated_at_delta=None,
            message_count_delta=0,
            last_message_source_after="middleware",
            tags_added=[],
        )
        self.assertFalse(evidence)
        self.assertIn("message_count_delta=0", reason)
        self.assertNotIn("last_message_source=middleware", reason)


class OutboundEvidenceTests(unittest.TestCase):
    def test_outbound_evidence_positive(self) -> None:
        evidence = _evaluate_outbound_evidence(
            message_count_delta=2, last_message_source_after="Middleware"
        )
        self.assertTrue(evidence["outbound_message_count_delta_ge_1"])
        self.assertTrue(evidence["outbound_last_message_source_middleware"])

    def test_outbound_evidence_negative(self) -> None:
        evidence = _evaluate_outbound_evidence(
            message_count_delta=0, last_message_source_after="agent"
        )
        self.assertFalse(evidence["outbound_message_count_delta_ge_1"])
        self.assertFalse(evidence["outbound_last_message_source_middleware"])

    def test_outbound_evidence_missing(self) -> None:
        evidence = _evaluate_outbound_evidence(
            message_count_delta=None, last_message_source_after=None
        )
        self.assertIsNone(evidence["outbound_message_count_delta_ge_1"])
        self.assertIsNone(evidence["outbound_last_message_source_middleware"])


class OperatorReplyEvidenceTests(unittest.TestCase):
    def test_operator_reply_evidence_present(self) -> None:
        evidence = _evaluate_operator_reply_evidence(
            latest_comment_is_operator=True, operator_reply_count_delta=1
        )
        self.assertTrue(evidence["operator_reply_present"])
        self.assertTrue(evidence["operator_reply_count_delta_ge_1"])

    def test_operator_reply_evidence_missing(self) -> None:
        evidence = _evaluate_operator_reply_evidence(
            latest_comment_is_operator=False, operator_reply_count_delta=None
        )
        self.assertFalse(evidence["operator_reply_present"])
        self.assertIsNone(evidence["operator_reply_count_delta_ge_1"])

    def test_operator_reply_evidence_unknown(self) -> None:
        evidence = _evaluate_operator_reply_evidence(
            latest_comment_is_operator=None, operator_reply_count_delta=None
        )
        self.assertIsNone(evidence["operator_reply_present"])
        self.assertIsNone(evidence["operator_reply_count_delta_ge_1"])


class SendMessageEvidenceTests(unittest.TestCase):
    def test_send_message_tag_present_and_added(self) -> None:
        evidence = _evaluate_send_message_evidence(
            tags_added=["mw-outbound-path-send-message"],
            post_tags=["mw-outbound-path-send-message"],
        )
        self.assertTrue(evidence["send_message_tag_present"])
        self.assertTrue(evidence["send_message_tag_added"])

    def test_send_message_tag_present_not_added(self) -> None:
        evidence = _evaluate_send_message_evidence(
            tags_added=[],
            post_tags=["mw-outbound-path-send-message"],
        )
        self.assertTrue(evidence["send_message_tag_present"])
        self.assertFalse(evidence["send_message_tag_added"])


class AllowlistEvidenceTests(unittest.TestCase):
    def test_allowlist_blocked_tag_present_and_added(self) -> None:
        evidence = _evaluate_allowlist_blocked_evidence(
            tags_added=["mw-outbound-blocked-allowlist"],
            post_tags=["mw-outbound-blocked-allowlist"],
        )
        self.assertTrue(evidence["allowlist_blocked_tag_present"])
        self.assertTrue(evidence["allowlist_blocked_tag_added"])

    def test_allowlist_blocked_tag_present_not_added(self) -> None:
        evidence = _evaluate_allowlist_blocked_evidence(
            tags_added=[],
            post_tags=["mw-outbound-blocked-allowlist"],
        )
        self.assertTrue(evidence["allowlist_blocked_tag_present"])
        self.assertFalse(evidence["allowlist_blocked_tag_added"])


class OutboundAttemptedTests(unittest.TestCase):
    def test_outbound_attempted_with_message_delta(self) -> None:
        attempted = _evaluate_outbound_attempted(
            message_count_delta=1,
            last_message_source_after=None,
            send_message_tag_present=None,
            allowlist_blocked_tag_present=None,
        )
        self.assertTrue(attempted)

    def test_outbound_attempted_with_allowlist_block(self) -> None:
        attempted = _evaluate_outbound_attempted(
            message_count_delta=0,
            last_message_source_after="agent",
            send_message_tag_present=False,
            allowlist_blocked_tag_present=True,
        )
        self.assertTrue(attempted)

    def test_outbound_attempted_false_when_all_signals_false(self) -> None:
        attempted = _evaluate_outbound_attempted(
            message_count_delta=0,
            last_message_source_after="agent",
            send_message_tag_present=False,
            allowlist_blocked_tag_present=False,
        )
        self.assertFalse(attempted)

    def test_outbound_attempted_unknown_when_no_signals(self) -> None:
        attempted = _evaluate_outbound_attempted(
            message_count_delta=None,
            last_message_source_after=None,
            send_message_tag_present=None,
            allowlist_blocked_tag_present=None,
        )
        self.assertIsNone(attempted)


class OutboundFailureClassificationTests(unittest.TestCase):
    def test_outbound_failure_blocked_by_allowlist(self) -> None:
        result = _classify_outbound_failure(
            allowlist_blocked_tag_present=True,
            outbound_attempted=True,
            outbound_message_count_ok=False,
            send_message_tag_present=False,
            require_outbound=True,
            require_send_message=True,
        )
        self.assertEqual(result, "blocked_by_allowlist")

    def test_outbound_failure_request_failed(self) -> None:
        result = _classify_outbound_failure(
            allowlist_blocked_tag_present=False,
            outbound_attempted=False,
            outbound_message_count_ok=False,
            send_message_tag_present=False,
            require_outbound=True,
            require_send_message=True,
        )
        self.assertEqual(result, "request_failed")

    def test_outbound_failure_none_when_not_required(self) -> None:
        result = _classify_outbound_failure(
            allowlist_blocked_tag_present=False,
            outbound_attempted=None,
            outbound_message_count_ok=None,
            send_message_tag_present=None,
            require_outbound=False,
            require_send_message=False,
        )
        self.assertIsNone(result)

    def test_outbound_failure_requires_send_message(self) -> None:
        result = _classify_outbound_failure(
            allowlist_blocked_tag_present=False,
            outbound_attempted=True,
            outbound_message_count_ok=True,
            send_message_tag_present=False,
            require_outbound=False,
            require_send_message=True,
        )
        self.assertEqual(result, "request_failed")

    def test_outbound_failure_requires_outbound(self) -> None:
        result = _classify_outbound_failure(
            allowlist_blocked_tag_present=False,
            outbound_attempted=True,
            outbound_message_count_ok=False,
            send_message_tag_present=True,
            require_outbound=True,
            require_send_message=False,
        )
        self.assertEqual(result, "request_failed")

    def test_outbound_failure_none_when_requirements_met(self) -> None:
        result = _classify_outbound_failure(
            allowlist_blocked_tag_present=False,
            outbound_attempted=True,
            outbound_message_count_ok=True,
            send_message_tag_present=True,
            require_outbound=True,
            require_send_message=True,
        )
        self.assertIsNone(result)


class SendMessageStatusTests(unittest.TestCase):
    def test_send_message_status_happy_path(self) -> None:
        status = _evaluate_send_message_status(
            post_tags=["mw-outbound-path-send-message"],
            send_message_tag_present=True,
            allowlist_blocked_tag_present=False,
            latest_comment_is_operator=True,
        )
        self.assertEqual(status, 200)

    def test_send_message_status_missing_tag(self) -> None:
        status = _evaluate_send_message_status(
            post_tags=[],
            send_message_tag_present=False,
            allowlist_blocked_tag_present=False,
            latest_comment_is_operator=True,
        )
        self.assertIsNone(status)

    def test_send_message_status_failure_tag(self) -> None:
        status = _evaluate_send_message_status(
            post_tags=["mw-send-message-failed"],
            send_message_tag_present=True,
            allowlist_blocked_tag_present=False,
            latest_comment_is_operator=True,
        )
        self.assertIsNone(status)

    def test_send_message_status_blocked_or_not_operator(self) -> None:
        status = _evaluate_send_message_status(
            post_tags=["mw-outbound-path-send-message"],
            send_message_tag_present=True,
            allowlist_blocked_tag_present=True,
            latest_comment_is_operator=True,
        )
        self.assertIsNone(status)
        status = _evaluate_send_message_status(
            post_tags=["mw-outbound-path-send-message"],
            send_message_tag_present=True,
            allowlist_blocked_tag_present=False,
            latest_comment_is_operator=False,
        )
        self.assertIsNone(status)


class SupportRoutingTests(unittest.TestCase):
    def test_support_routing_tag_forces_support(self) -> None:
        result = _evaluate_support_routing(
            routing_tags=["route-email-support-team"],
            routing_department=None,
            routing_intent="order_status_tracking",
        )
        self.assertTrue(result["routed_to_support"])
        self.assertTrue(result["support_tag_present"])

    def test_support_routing_department_for_non_order_status(self) -> None:
        result = _evaluate_support_routing(
            routing_tags=["mw-routing-applied"],
            routing_department="Email Support Team",
            routing_intent="cancel_subscription",
        )
        self.assertTrue(result["routed_to_support"])
        self.assertFalse(result["support_tag_present"])

    def test_support_routing_order_status_without_tag(self) -> None:
        result = _evaluate_support_routing(
            routing_tags=["mw-routing-applied"],
            routing_department="Email Support Team",
            routing_intent="order_status_tracking",
        )
        self.assertFalse(result["routed_to_support"])

    def test_support_routing_ticket_tags(self) -> None:
        result = _evaluate_support_routing(
            routing_tags=["mw-routing-applied"],
            routing_department="Email Support Team",
            routing_intent="order_status_tracking",
            ticket_tags=["route-email-support-team"],
        )
        self.assertTrue(result["routed_to_support"])
        self.assertTrue(result["support_tag_present"])


class OrderMatchEvidenceTests(unittest.TestCase):
    def test_order_match_success_with_draft_action(self) -> None:
        result = _evaluate_order_match_evidence(
            routing_tags=["mw-routing-applied"],
            draft_action_present=True,
            routing_intent="order_status_tracking",
        )
        self.assertTrue(result["order_match_success"])
        self.assertIsNone(result["order_match_failure_reason"])

    def test_order_match_failure_from_missing_context_tag(self) -> None:
        result = _evaluate_order_match_evidence(
            routing_tags=[
                "mw-order-lookup-failed",
                "mw-order-lookup-missing:created_at",
            ],
            draft_action_present=False,
            routing_intent="order_status_tracking",
        )
        self.assertFalse(result["order_match_success"])
        self.assertEqual(
            result["order_match_failure_reason"], "missing_context:created_at"
        )

    def test_order_match_failure_without_missing_tag(self) -> None:
        result = _evaluate_order_match_evidence(
            routing_tags=["mw-order-lookup-failed"],
            draft_action_present=False,
            routing_intent="order_status_tracking",
        )
        self.assertFalse(result["order_match_success"])
        self.assertEqual(result["order_match_failure_reason"], "order_lookup_failed")

    def test_order_match_no_signal_returns_none(self) -> None:
        result = _evaluate_order_match_evidence(
            routing_tags=["mw-routing-applied"],
            draft_action_present=False,
            routing_intent="order_status_tracking",
        )
        self.assertIsNone(result["order_match_success"])
        self.assertIsNone(result["order_match_failure_reason"])

    def test_order_match_ignored_for_non_order_status(self) -> None:
        result = _evaluate_order_match_evidence(
            routing_tags=["mw-routing-applied"],
            draft_action_present=False,
            routing_intent="refund_request",
        )
        self.assertIsNone(result["order_match_success"])
        self.assertIsNone(result["order_match_failure_reason"])


class OrderMatchResolutionTests(unittest.TestCase):
    def test_order_resolution_is_order_number(self) -> None:
        self.assertTrue(
            _order_resolution_is_order_number(
                {"resolvedBy": "richpanel_order_number"}
            )
        )
        self.assertTrue(
            _order_resolution_is_order_number(
                {"resolvedBy": "richpanel_order_number_then_shopify_identity"}
            )
        )

    def test_order_resolution_is_not_order_number(self) -> None:
        self.assertFalse(
            _order_resolution_is_order_number({"resolvedBy": "shopify_email_only"})
        )
        self.assertFalse(_order_resolution_is_order_number({"resolvedBy": "no_match"}))

    def test_order_resolution_is_order_number_none(self) -> None:
        self.assertIsNone(_order_resolution_is_order_number(None))
        self.assertIsNone(_order_resolution_is_order_number({}))

    def test_extract_order_match_method_from_resolution(self) -> None:
        method = _extract_order_match_method(
            order_match_success=True,
            order_resolution={"resolvedBy": "shopify_email_name"},
        )
        self.assertEqual(method, "name_email")
        method = _extract_order_match_method(
            order_match_success=True,
            order_resolution={"resolvedBy": "shopify_email_only"},
        )
        self.assertEqual(method, "email_only")
        method = _extract_order_match_method(
            order_match_success=True,
            order_resolution={"resolvedBy": "richpanel_order_number"},
        )
        self.assertEqual(method, "order_number")

    def test_extract_order_match_method_handles_failure(self) -> None:
        method = _extract_order_match_method(
            order_match_success=False, order_resolution={"resolvedBy": "no_match"}
        )
        self.assertEqual(method, "none")

    def test_extract_order_resolution_from_actions(self) -> None:
        actions = [
            {"type": "noop"},
            {
                "type": "order_status_draft_reply",
                "parameters": {"order_summary": {"order_resolution": {"resolvedBy": "x"}}},
            },
        ]
        resolution = _extract_order_resolution_from_actions(actions)
        self.assertEqual(resolution, {"resolvedBy": "x"})

    def test_extract_order_resolution_from_actions_handles_missing(self) -> None:
        resolution = _extract_order_resolution_from_actions([{"type": "noop"}])
        self.assertIsNone(resolution)

    def test_normalize_optional_text(self) -> None:
        self.assertEqual(_normalize_optional_text("  hello "), "hello")
        self.assertEqual(_normalize_optional_text(123), "123")
        class _BadStr:
            def __str__(self) -> str:
                raise ValueError("boom")
        self.assertEqual(_normalize_optional_text(_BadStr()), "")

    def test_probe_order_resolution_from_ticket(self) -> None:
        payload = {"customer_profile": {"email": "person@example.com", "name": "Test"}}
        with patch(
            "dev_e2e_smoke.lookup_order_summary",
            return_value={"order_resolution": {"resolvedBy": "shopify_email_only"}},
        ):
            resolution = _probe_order_resolution_from_ticket(
                ticket_payload=payload,
                allow_network=True,
                safe_mode=True,
                automation_enabled=False,
            )
        self.assertEqual(resolution, {"resolvedBy": "shopify_email_only"})

    def test_probe_order_resolution_from_ticket_requires_email(self) -> None:
        resolution = _probe_order_resolution_from_ticket(
            ticket_payload={"customer_profile": {"name": "No Email"}},
            allow_network=True,
            safe_mode=True,
            automation_enabled=True,
        )
        self.assertIsNone(resolution)

    def test_detect_order_match_by_number_success(self) -> None:
        payload = {"order_number": "12345", "tracking_number": "TRACK-123"}
        with patch(
            "dev_e2e_smoke.lookup_order_summary",
            return_value={"order_resolution": {"resolvedBy": "richpanel_order_number"}},
        ):
            result = _detect_order_match_by_number(
                payload=payload,
                allow_network=True,
                safe_mode=False,
                automation_enabled=True,
            )
        self.assertTrue(result)

    def test_detect_order_match_by_number_missing_order(self) -> None:
        result = _detect_order_match_by_number(
            payload={"customer_message": "order status"},
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
        )
        self.assertIsNone(result)

    def test_detect_order_match_by_number_network_disabled(self) -> None:
        result = _detect_order_match_by_number(
            payload={"order_number": "12345"},
            allow_network=False,
            safe_mode=False,
            automation_enabled=True,
        )
        self.assertIsNone(result)

    def test_detect_order_match_by_number_exception(self) -> None:
        with patch(
            "dev_e2e_smoke.lookup_order_summary", side_effect=Exception("boom")
        ):
            result = _detect_order_match_by_number(
                payload={"order_number": "12345"},
                allow_network=True,
                safe_mode=False,
                automation_enabled=True,
            )
        self.assertIsNone(result)

    def test_detect_order_match_by_number_non_dict_summary(self) -> None:
        with patch("dev_e2e_smoke.lookup_order_summary", return_value=["oops"]):
            result = _detect_order_match_by_number(
                payload={"order_number": "12345"},
                allow_network=True,
                safe_mode=False,
                automation_enabled=True,
            )
        self.assertIsNone(result)


class ReplyContentFlagsTests(unittest.TestCase):
    def test_reply_contains_tracking_url(self) -> None:
        body = "Tracking link: https://tracking.example.com/track/ABC123"
        self.assertTrue(_reply_contains_tracking_url(body))
        self.assertFalse(_reply_contains_tracking_url(None))

    def test_reply_contains_tracking_url_with_expected(self) -> None:
        body = "Link: https://tracking.example.com/track/ABC123"
        self.assertTrue(
            _reply_contains_tracking_url(body, expected_url="ABC123")
        )
        self.assertFalse(
            _reply_contains_tracking_url("No url here", expected_url="missing")
        )

    def test_reply_contains_tracking_number_like(self) -> None:
        body = "Tracking number: 1Z999AA10123456784"
        self.assertTrue(_reply_contains_tracking_number_like(body))
        self.assertTrue(
            _reply_contains_tracking_number_like(
                "Code: ABC12345", expected_number="ABC12345"
            )
        )
        self.assertFalse(
            _reply_contains_tracking_number_like("Tracking: N/A")
        )
        self.assertFalse(_reply_contains_tracking_number_like(None))

    def test_reply_contains_tracking_url_false(self) -> None:
        body = "Tracking link: (not available)"
        self.assertFalse(_reply_contains_tracking_url(body))

    def test_reply_contains_eta_date_iso(self) -> None:
        body = "Your order was placed on 2026-02-04. It should arrive soon."
        self.assertTrue(_reply_contains_eta_date_like(body))
        self.assertFalse(_reply_contains_eta_date_like("No dates here"))
        self.assertFalse(_reply_contains_eta_date_like(None))

    def test_collect_reply_body_candidates_and_flags(self) -> None:
        candidates = _collect_reply_body_candidates(
            latest_reply_body=None,
            draft_replies=None,
            computed_draft_body=(
                "Computed reply with 2026-02-04, tracking number: ABC12345, and "
                "https://tracking.example.com/t/1"
            ),
        )
        self.assertEqual(len(candidates), 1)
        contains_tracking, contains_tracking_number, contains_eta = (
            _evaluate_reply_content_flags(
                candidates=candidates,
                expected_tracking_url=None,
                expected_tracking_number=None,
            )
        )
        self.assertTrue(contains_tracking)
        self.assertTrue(contains_tracking_number)
        self.assertTrue(contains_eta)

    def test_collect_reply_body_candidates_from_drafts(self) -> None:
        candidates = _collect_reply_body_candidates(
            latest_reply_body="",
            draft_replies=[{"body": "Draft body"}, "skip", {"body": "  "}],
            computed_draft_body="Fallback",
        )
        self.assertEqual(candidates, ["Draft body"])
        contains_tracking, contains_tracking_number, contains_eta = (
            _evaluate_reply_content_flags(
                candidates=candidates,
                expected_tracking_url="missing",
                expected_tracking_number="missing",
            )
        )
        self.assertFalse(contains_tracking)
        self.assertFalse(contains_tracking_number)
        self.assertFalse(contains_eta)

    def test_reply_content_flags_empty_candidates(self) -> None:
        contains_tracking, contains_tracking_number, contains_eta = (
            _evaluate_reply_content_flags(
                candidates=[],
                expected_tracking_url=None,
                expected_tracking_number=None,
            )
        )
        self.assertFalse(contains_tracking)
        self.assertFalse(contains_tracking_number)
        self.assertFalse(contains_eta)

    def test_collect_reply_body_candidates_prefers_latest(self) -> None:
        candidates = _collect_reply_body_candidates(
            latest_reply_body="Latest body",
            draft_replies="not-a-list",  # type: ignore[arg-type]
            computed_draft_body="Fallback body",
        )
        self.assertEqual(candidates, ["Latest body"])


class AllowlistSkipTests(unittest.TestCase):
    def test_should_skip_allowlist_blocked_when_unconfigured(self) -> None:
        reason = _should_skip_allowlist_blocked(
            require_allowlist_blocked=True, allowlist_configured=False
        )
        self.assertEqual(reason, "allowlist_not_configured")

    def test_should_not_skip_allowlist_blocked_when_configured(self) -> None:
        reason = _should_skip_allowlist_blocked(
            require_allowlist_blocked=True, allowlist_configured=True
        )
        self.assertIsNone(reason)

    def test_unexpected_outbound_blocked(self) -> None:
        unexpected = _unexpected_outbound_blocked(
            fail_on_outbound_block=True,
            allowlist_blocked_tag_present=True,
            require_allowlist_blocked=False,
        )
        self.assertTrue(unexpected)

    def test_unexpected_outbound_blocked_ignored_when_required(self) -> None:
        unexpected = _unexpected_outbound_blocked(
            fail_on_outbound_block=True,
            allowlist_blocked_tag_present=True,
            require_allowlist_blocked=True,
        )
        self.assertFalse(unexpected)


class SkipProofPayloadTests(unittest.TestCase):
    def test_build_skip_proof_payload_has_status_and_fields(self) -> None:
        payload = _build_skip_proof_payload(
            run_id="RUN_SKIP",
            env_name="dev",
            region="us-east-2",
            scenario="allowlist_blocked",
            skip_reason="allowlist_not_configured",
            allowlist_config={"allowlist_emails_count": 0},
        )
        self.assertEqual(payload["result"]["status"], "SKIP")
        self.assertEqual(payload["result"]["classification"], "SKIP")
        self.assertIn("proof_fields", payload)
        self.assertIn("ticket_channel", payload["proof_fields"])
        self.assertIn("intent_after", payload["proof_fields"])
        self.assertIsNone(payload["proof_fields"]["outbound_attempted"])
        self.assertIn("outbound_send_message_status", payload["proof_fields"])
        self.assertIn("outbound_endpoint_used", payload["proof_fields"])
        self.assertIn("send_message_used", payload["proof_fields"])
        self.assertIn("send_message_status_code", payload["proof_fields"])
        self.assertIn("reply_contains_tracking_url", payload["proof_fields"])
        self.assertIn("reply_contains_tracking_number_like", payload["proof_fields"])
        self.assertIn("reply_contains_eta_date_like", payload["proof_fields"])
        self.assertIn("latest_comment_is_operator", payload["proof_fields"])
        self.assertIn("latest_comment_source", payload["proof_fields"])
        self.assertIn("order_match_method", payload["proof_fields"])
        self.assertIn("order_match_by_number", payload["proof_fields"])
        self.assertIn("operator_reply_confirmed", payload["proof_fields"])
        self.assertIn("operator_reply_reason", payload["proof_fields"])
        self.assertIn("openai_routing_response_id", payload["proof_fields"])
        self.assertIn("openai_rewrite_response_id", payload["proof_fields"])
        self.assertIn("final_route", payload["proof_fields"])
        self.assertIn("routing_ticket_excerpt_redacted", payload["proof_fields"])


class AllowlistConfigTests(unittest.TestCase):
    def test_parse_allowlist_entries_empty(self) -> None:
        entries = _parse_allowlist_entries(None)
        self.assertEqual(entries, set())

    def test_parse_allowlist_entries_basic(self) -> None:
        entries = _parse_allowlist_entries("A@example.com, ,b@example.com")
        self.assertEqual(entries, {"a@example.com", "b@example.com"})

    def test_parse_allowlist_entries_strip_at(self) -> None:
        entries = _parse_allowlist_entries("@example.com,@foo.com", strip_at=True)
        self.assertEqual(entries, {"example.com", "foo.com"})

    def test_to_bool_parses_truthy_values(self) -> None:
        for value in ("1", "true", "yes", "on", "TRUE"):
            self.assertTrue(_to_bool(value))
        self.assertFalse(_to_bool(None))
        self.assertFalse(_to_bool("false"))

    def test_fetch_lambda_allowlist_config(self) -> None:
        class _LambdaClient:
            def get_function_configuration(self, **_: Any) -> dict:
                return {
                    "Environment": {
                        "Variables": {
                            "MW_OUTBOUND_ALLOWLIST_EMAILS": "a@example.com,b@example.com",
                            "MW_OUTBOUND_ALLOWLIST_DOMAINS": "@example.com",
                            "RICHPANEL_OUTBOUND_ENABLED": "true",
                        }
                    }
                }

        result = _fetch_lambda_allowlist_config(
            _LambdaClient(), function_name="rp-mw-dev-worker"
        )
        self.assertTrue(result["allowlist_configured"])
        self.assertEqual(result["allowlist_emails_count"], 2)
        self.assertEqual(result["allowlist_domains_count"], 1)
        self.assertTrue(result["outbound_enabled"])

    def test_fetch_lambda_allowlist_config_error(self) -> None:
        class _FailLambdaClient:
            def get_function_configuration(self, **_: Any) -> dict:
                raise ClientError(
                    {"Error": {"Code": "AccessDenied", "Message": "denied"}},
                    "GetFunctionConfiguration",
                )

        with self.assertRaises(SmokeFailure):
            _fetch_lambda_allowlist_config(
                _FailLambdaClient(), function_name="rp-mw-dev-worker"
            )


class ProofPayloadWriteTests(unittest.TestCase):
    def test_write_proof_payload_pii_safe(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "proof.json"
            payload = {
                "result": {
                    "status": "PASS",
                    "classification": "PASS",
                    "criteria": {"pii_safe": True},
                    "criteria_details": [{"name": "pii_safe", "value": True}],
                }
            }
            _write_proof_payload(path, payload)
            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored["result"]["status"], "PASS")
            self.assertTrue(stored["result"]["criteria"]["pii_safe"])

    def test_write_proof_payload_marks_pii_fail(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "proof.json"
            payload = {
                "inputs": {
                    "command": "python scripts/dev_e2e_smoke.py --ticket-number 123"
                },
                "result": {
                    "status": "PASS",
                    "classification": "PASS",
                    "criteria": {"pii_safe": True},
                    "criteria_details": [{"name": "pii_safe", "value": True}],
                },
            }
            _write_proof_payload(path, payload)
            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored["result"]["status"], "FAIL")
            self.assertEqual(stored["result"]["classification"], "FAIL")
            self.assertFalse(stored["result"]["criteria"]["pii_safe"])
            self.assertFalse(stored["result"]["criteria_details"][0]["value"])


class PayloadBuilderTests(unittest.TestCase):
    def test_build_payload_not_order_status(self) -> None:
        payload = build_payload(
            "evt-123",
            conversation_id="conv-1",
            run_id="RUN",
            scenario="not_order_status",
        )
        self.assertEqual(payload["scenario_name"], "not_order_status")
        self.assertEqual(payload["scenario"], "not_order_status")
        self.assertIn("customer_message", payload)

    def test_build_payload_order_status_tracking(self) -> None:
        payload = build_payload(
            "evt-789",
            conversation_id="conv-3",
            run_id="RUN",
            scenario="order_status_tracking",
        )
        self.assertEqual(payload["scenario_name"], "order_status_tracking")
        self.assertIn("order_id", payload)
        self.assertIn("tracking_number", payload)

    def test_build_payload_order_status_includes_order_number(self) -> None:
        payload = build_payload(
            "evt-789",
            conversation_id="conv-3",
            run_id="RUN",
            scenario="order_status_tracking",
            order_number="12345",
        )
        self.assertEqual(payload["order_number"], "12345")

    def test_build_payload_order_status_no_match(self) -> None:
        payload = build_payload(
            "evt-456",
            conversation_id="conv-2",
            run_id="RUN",
            scenario="order_status_no_match",
        )
        self.assertEqual(payload["scenario_name"], "order_status_no_match")
        self.assertTrue(payload["order_number"].startswith("FAKE-"))

    def test_build_payload_order_status_fallback_email_match(self) -> None:
        payload = build_payload(
            "evt-457",
            conversation_id="conv-3",
            run_id="RUN",
            scenario="order_status_fallback_email_match",
        )
        self.assertEqual(
            payload["scenario_name"], "order_status_fallback_email_match"
        )
        self.assertNotIn("order_number", payload)

    def test_build_payload_baseline_has_no_scenario(self) -> None:
        payload = build_payload(
            "evt-000",
            conversation_id="conv-0",
            run_id="RUN",
            scenario="baseline",
        )
        self.assertNotIn("scenario_name", payload)
        self.assertNotIn("scenario", payload)


class ParseArgsTests(unittest.TestCase):
    def test_parse_args_accepts_allowlist_flags(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "dev_e2e_smoke.py",
                "--region",
                "us-east-2",
                "--scenario",
                "allowlist_blocked",
                "--require-allowlist-blocked",
                "--fail-on-outbound-block",
            ],
        ):
            args = parse_args()
        self.assertEqual(args.scenario, "allowlist_blocked")
        self.assertTrue(args.require_allowlist_blocked)
        self.assertTrue(args.fail_on_outbound_block)

    def test_parse_args_accepts_order_match_by_number_flag(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "dev_e2e_smoke.py",
                "--region",
                "us-east-2",
                "--require-order-match-by-number",
            ],
        ):
            args = parse_args()
        self.assertTrue(args.require_order_match_by_number)

    def test_parse_args_accepts_order_number(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "dev_e2e_smoke.py",
                "--region",
                "us-east-2",
                "--order-number",
                "12345",
            ],
        ):
            args = parse_args()
        self.assertEqual(args.order_number, "12345")

    def test_parse_args_accepts_require_send_message_used(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "dev_e2e_smoke.py",
                "--region",
                "us-east-2",
                "--require-send-message-used",
            ],
        ):
            args = parse_args()
        self.assertTrue(args.require_send_message_used)

    def test_parse_args_accepts_require_email_channel(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "dev_e2e_smoke.py",
                "--region",
                "us-east-2",
                "--require-email-channel",
            ],
        ):
            args = parse_args()
        self.assertTrue(args.require_email_channel)


class TestRequirementFlagResolution(unittest.TestCase):
    def test_non_order_status_allows_explicit_email_requirements(self) -> None:
        args = SimpleNamespace(
            require_openai_routing=None,
            require_openai_rewrite=None,
            require_order_match_by_number=None,
            require_outbound=True,
            require_email_channel=True,
            require_operator_reply=True,
            require_send_message=True,
            require_send_message_used=True,
            require_allowlist_blocked=False,
        )
        flags = _resolve_requirement_flags(
            args,
            order_status_mode=False,
            negative_scenario=False,
            allowlist_blocked_mode=False,
            order_status_no_match_mode=False,
        )
        self.assertTrue(flags["require_outbound"])
        self.assertTrue(flags["require_email_channel"])
        self.assertTrue(flags["require_operator_reply"])
        self.assertTrue(flags["require_send_message"])
        self.assertTrue(flags["require_send_message_used"])
        self.assertFalse(flags["require_openai_routing"])
        self.assertFalse(flags["require_openai_rewrite"])
        self.assertFalse(flags["require_order_match_by_number"])

    def test_non_order_status_defaults_disable_email_requirements(self) -> None:
        args = SimpleNamespace(
            require_openai_routing=None,
            require_openai_rewrite=None,
            require_order_match_by_number=None,
            require_outbound=None,
            require_email_channel=None,
            require_operator_reply=None,
            require_send_message=None,
            require_send_message_used=None,
            require_allowlist_blocked=None,
        )
        flags = _resolve_requirement_flags(
            args,
            order_status_mode=False,
            negative_scenario=False,
            allowlist_blocked_mode=False,
            order_status_no_match_mode=False,
        )
        self.assertFalse(flags["require_outbound"])
        self.assertFalse(flags["require_email_channel"])
        self.assertFalse(flags["require_operator_reply"])
        self.assertFalse(flags["require_send_message"])
        self.assertFalse(flags["require_send_message_used"])
        self.assertFalse(flags["require_allowlist_blocked"])
        self.assertFalse(flags["require_order_match_by_number"])

    def test_allowlist_blocked_overrides_requirements(self) -> None:
        args = SimpleNamespace(
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_order_match_by_number=True,
            require_outbound=True,
            require_email_channel=True,
            require_operator_reply=True,
            require_send_message=True,
            require_send_message_used=True,
            require_allowlist_blocked=None,
        )
        flags = _resolve_requirement_flags(
            args,
            order_status_mode=True,
            negative_scenario=False,
            allowlist_blocked_mode=True,
            order_status_no_match_mode=False,
        )
        self.assertTrue(flags["require_allowlist_blocked"])
        self.assertFalse(flags["require_outbound"])
        self.assertFalse(flags["require_email_channel"])
        self.assertFalse(flags["require_operator_reply"])
        self.assertFalse(flags["require_send_message"])
        self.assertFalse(flags["require_send_message_used"])
        self.assertFalse(flags["require_openai_routing"])
        self.assertFalse(flags["require_openai_rewrite"])
        self.assertFalse(flags["require_order_match_by_number"])

    def test_negative_scenario_disables_order_match_requirement(self) -> None:
        args = SimpleNamespace(
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_order_match_by_number=True,
            require_outbound=True,
            require_email_channel=True,
            require_operator_reply=True,
            require_send_message=True,
            require_send_message_used=True,
            require_allowlist_blocked=False,
        )
        flags = _resolve_requirement_flags(
            args,
            order_status_mode=True,
            negative_scenario=True,
            allowlist_blocked_mode=False,
            order_status_no_match_mode=False,
        )
        self.assertFalse(flags["require_order_match_by_number"])

    def test_no_match_mode_disables_order_match_requirement(self) -> None:
        args = SimpleNamespace(
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_order_match_by_number=True,
            require_outbound=True,
            require_email_channel=True,
            require_operator_reply=True,
            require_send_message=True,
            require_send_message_used=True,
            require_allowlist_blocked=False,
        )
        flags = _resolve_requirement_flags(
            args,
            order_status_mode=True,
            negative_scenario=False,
            allowlist_blocked_mode=False,
            order_status_no_match_mode=True,
        )
        self.assertFalse(flags["require_order_match_by_number"])


class RoutingValidationTests(unittest.TestCase):
    def test_validate_routing_includes_optional_fields(self) -> None:
        record = {
            "routing": {
                "category": "general",
                "tags": ["mw-routing-applied"],
                "reason": "test",
                "intent": "refund_request",
                "department": "Email Support Team",
            }
        }
        validated = validate_routing(record, label="test")
        self.assertEqual(validated["intent"], "refund_request")
        self.assertEqual(validated["department"], "Email Support Team")


class OperatorSendMessageHelperTests(unittest.TestCase):
    def test_compute_operator_reply_metrics(self) -> None:
        metrics = _compute_operator_reply_metrics(
            {"operator_reply_count": 1},
            {
                "operator_reply_count": 3,
                "operator_reply_present": True,
                "latest_comment_is_operator": True,
            },
        )
        self.assertEqual(metrics["operator_reply_count_before"], 1)
        self.assertEqual(metrics["operator_reply_count_after"], 3)
        self.assertEqual(metrics["operator_reply_count_delta"], 2)
        self.assertTrue(metrics["operator_reply_present"])
        self.assertTrue(metrics["latest_comment_is_operator"])

    def test_build_operator_send_message_proof_fields(self) -> None:
        fields = _build_operator_send_message_proof_fields(
            operator_reply_present=True,
            operator_reply_count_delta=1,
            latest_comment_is_operator=True,
            operator_reply_required=True,
            operator_reply_confirmed=True,
            operator_reply_reason="confirmed",
            send_message_tag_present=True,
            send_message_tag_added=False,
            send_message_path_required=True,
            send_message_path_confirmed=True,
            send_message_used=True,
            send_message_status_code=200,
        )
        self.assertEqual(fields["operator_reply_present"], True)
        self.assertEqual(fields["operator_reply_count_delta"], 1)
        self.assertEqual(fields["latest_comment_is_operator"], True)
        self.assertEqual(fields["operator_reply_required"], True)
        self.assertEqual(fields["operator_reply_confirmed"], True)
        self.assertEqual(fields["operator_reply_reason"], "confirmed")
        self.assertEqual(fields["send_message_tag_present"], True)
        self.assertEqual(fields["send_message_tag_added"], False)
        self.assertEqual(fields["send_message_path_required"], True)
        self.assertEqual(fields["send_message_path_confirmed"], True)
        self.assertEqual(fields["send_message_used"], True)
        self.assertEqual(fields["send_message_status_code"], 200)

    def test_build_operator_send_message_richpanel_fields(self) -> None:
        fields = _build_operator_send_message_richpanel_fields(
            operator_reply_present=False,
            operator_reply_count_before=0,
            operator_reply_count_after=1,
            operator_reply_count_delta=1,
            latest_comment_is_operator=False,
            send_message_tag_present=True,
            send_message_tag_added=True,
        )
        self.assertFalse(fields["operator_reply_present"])
        self.assertEqual(fields["operator_reply_count_before"], 0)
        self.assertEqual(fields["operator_reply_count_after"], 1)
        self.assertEqual(fields["operator_reply_count_delta"], 1)
        self.assertFalse(fields["latest_comment_is_operator"])
        self.assertTrue(fields["send_message_tag_present"])
        self.assertTrue(fields["send_message_tag_added"])

    def test_build_operator_send_message_criteria(self) -> None:
        criteria = _build_operator_send_message_criteria(
            operator_reply_present_ok=True,
            operator_reply_delta_ok=False,
            send_message_tag_present_ok=True,
            send_message_tag_added_ok=False,
            send_message_used_ok=True,
        )
        self.assertTrue(criteria["operator_reply_present"])
        self.assertFalse(criteria["operator_reply_count_delta_ge_1"])
        self.assertTrue(criteria["send_message_tag_present"])
        self.assertFalse(criteria["send_message_tag_added"])
        self.assertTrue(criteria["send_message_used"])

    def test_append_operator_send_message_criteria_details(self) -> None:
        required_checks: list[bool] = []
        criteria_details: list[dict[str, Any]] = []
        _append_operator_send_message_criteria_details(
            criteria_details=criteria_details,
            required_checks=required_checks,
            order_status_mode=True,
            require_operator_reply=True,
            require_send_message=True,
            require_send_message_used=True,
            operator_reply_present_ok=True,
            send_message_tag_present_ok=True,
            send_message_tag_added_ok=False,
            send_message_used_ok=True,
        )
        self.assertTrue(required_checks)
        names = [entry["name"] for entry in criteria_details]
        self.assertIn("operator_reply_present", names)
        self.assertIn("send_message_tag_present", names)
        self.assertIn("send_message_tag_added", names)
        self.assertIn("send_message_used", names)

    def test_append_operator_reply_required_unknown_fails(self) -> None:
        required_checks: list[bool] = []
        criteria_details: list[dict[str, Any]] = []
        _append_operator_send_message_criteria_details(
            criteria_details=criteria_details,
            required_checks=required_checks,
            order_status_mode=True,
            require_operator_reply=True,
            require_send_message=False,
            require_send_message_used=False,
            operator_reply_present_ok=None,
            send_message_tag_present_ok=None,
            send_message_tag_added_ok=None,
            send_message_used_ok=None,
        )
        self.assertEqual(required_checks, [False])
        self.assertIsNone(criteria_details[0]["value"])

    def test_append_send_message_required_missing_fails(self) -> None:
        required_checks: list[bool] = []
        criteria_details: list[dict[str, Any]] = []
        _append_operator_send_message_criteria_details(
            criteria_details=criteria_details,
            required_checks=required_checks,
            order_status_mode=True,
            require_operator_reply=False,
            require_send_message=True,
            require_send_message_used=False,
            operator_reply_present_ok=None,
            send_message_tag_present_ok=False,
            send_message_tag_added_ok=None,
            send_message_used_ok=None,
        )
        self.assertEqual(required_checks, [False])
        names = [entry["name"] for entry in criteria_details]
        self.assertIn("send_message_tag_present", names)

    def test_append_operator_send_message_criteria_details_skips_non_order_status(
        self,
    ) -> None:
        required_checks: list[bool] = []
        criteria_details: list[dict[str, Any]] = []
        _append_operator_send_message_criteria_details(
            criteria_details=criteria_details,
            required_checks=required_checks,
            order_status_mode=False,
            require_operator_reply=True,
            require_send_message=True,
            require_send_message_used=True,
            operator_reply_present_ok=True,
            send_message_tag_present_ok=True,
            send_message_tag_added_ok=True,
            send_message_used_ok=True,
        )
        self.assertEqual(criteria_details, [])
        self.assertEqual(required_checks, [])


class OutboundResultHelperTests(unittest.TestCase):
    def test_extract_outbound_result_prefers_state(self) -> None:
        state_item = {"outbound_result": {"sent": True, "reason": "sent"}}
        audit_item = {"outbound_result": {"sent": False, "reason": "skipped"}}
        self.assertEqual(
            _extract_outbound_result(state_item, audit_item),
            state_item["outbound_result"],
        )

    def test_extract_outbound_result_falls_back_to_audit(self) -> None:
        audit_item = {"outbound_result": {"sent": False, "reason": "skipped"}}
        self.assertEqual(
            _extract_outbound_result({}, audit_item),
            audit_item["outbound_result"],
        )
        self.assertIsNone(_extract_outbound_result({}, {}))

    def test_send_message_used_from_outbound_result(self) -> None:
        self.assertIsNone(_send_message_used_from_outbound_result(None))
        self.assertTrue(
            _send_message_used_from_outbound_result(
                {"responses": [{"action": "send_message", "status": 200}]}
            )
        )
        self.assertFalse(
            _send_message_used_from_outbound_result(
                {"responses": [{"action": "add_tag", "status": 200}]}
            )
        )
        self.assertIsNone(
            _send_message_used_from_outbound_result({"responses": "bad"})
        )

    def test_send_message_status_from_outbound_result(self) -> None:
        self.assertIsNone(_send_message_status_from_outbound_result(None))
        self.assertEqual(
            _send_message_status_from_outbound_result(
                {"responses": [{"action": "send_message", "status": "202"}]}
            ),
            202,
        )
        self.assertIsNone(
            _send_message_status_from_outbound_result({"responses": "bad"})
        )
        self.assertIsNone(
            _send_message_status_from_outbound_result(
                {"responses": ["bad", {"action": "add_tag", "status": 200}]}
            )
        )
        self.assertIsNone(
            _send_message_status_from_outbound_result(
                {"responses": [{"action": "send_message", "status": 200.5}]}
            )
        )

    def test_resolve_send_message_used_fallbacks(self) -> None:
        self.assertTrue(
            _resolve_send_message_used(
                outbound_result=None, send_message_tag_present=True
            )
        )
        self.assertIsNone(
            _resolve_send_message_used(
                outbound_result=None, send_message_tag_present=None
            )
        )

    def test_resolve_send_message_status_code_fallbacks(self) -> None:
        self.assertEqual(
            _resolve_send_message_status_code(
                outbound_result=None, outbound_send_message_status=200
            ),
            200,
        )
        self.assertEqual(
            _resolve_send_message_status_code(
                outbound_result={
                    "responses": [{"action": "send_message", "status": 201}]
                },
                outbound_send_message_status=200,
            ),
            201,
        )

    def test_resolve_outbound_endpoint_used(self) -> None:
        self.assertIsNone(_resolve_outbound_endpoint_used(send_message_used=None))
        self.assertIsNone(_resolve_outbound_endpoint_used(send_message_used=False))
        self.assertEqual(
            _resolve_outbound_endpoint_used(send_message_used=True), "/send-message"
        )

    def test_resolve_operator_reply_reason_variants(self) -> None:
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=True,
                require_operator_reply=True,
                outbound_reason=None,
                send_message_used=True,
                latest_comment_is_operator=True,
            ),
            "confirmed",
        )
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=None,
                require_operator_reply=False,
                outbound_reason=None,
                send_message_used=None,
                latest_comment_is_operator=None,
            ),
            "not_required",
        )
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=None,
                require_operator_reply=True,
                outbound_reason="send_message_failed",
                send_message_used=None,
                latest_comment_is_operator=None,
            ),
            "send_message_failed",
        )
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=None,
                require_operator_reply=True,
                outbound_reason=None,
                send_message_used=False,
                latest_comment_is_operator=None,
            ),
            "send_message_not_used",
        )
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=None,
                require_operator_reply=True,
                outbound_reason=None,
                send_message_used=True,
                latest_comment_is_operator=False,
            ),
            "latest_comment_not_operator",
        )
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=None,
                require_operator_reply=True,
                outbound_reason=None,
                send_message_used=True,
                latest_comment_is_operator=None,
            ),
            "operator_flag_missing",
        )
        self.assertEqual(
            _resolve_operator_reply_reason(
                operator_reply_confirmed=None,
                require_operator_reply=True,
                outbound_reason=None,
                send_message_used=True,
                latest_comment_is_operator=True,
            ),
            "unconfirmed",
        )


class TicketSnapshotTests(unittest.TestCase):
    def test_fetch_ticket_snapshot_comment_fallback(self) -> None:
        payload = {
            "ticket": {
                "id": "ticket-1",
                "status": "OPEN",
                "tags": [],
                "comments": [
                    {"type": "Comment", "is_operator": False},
                    {"type": "text", "is_operator": False},
                ],
            }
        }

        class _Resp:
            status_code = 200
            dry_run = False

            def json(self) -> dict:
                return payload

        class _Exec:
            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp()

        result = _fetch_ticket_snapshot(
            cast(Any, _Exec()),
            "ticket-1",
            allow_network=True,
        )
        self.assertEqual(result.get("message_count"), 2)
        self.assertEqual(result.get("last_message_source"), "unknown")
        self.assertFalse(result.get("operator_reply_present"))
        self.assertEqual(result.get("operator_reply_count"), 0)
        self.assertFalse(result.get("latest_comment_is_operator"))

    def test_fetch_ticket_snapshot_operator_latest_comment(self) -> None:
        payload = {
            "ticket": {
                "id": "ticket-2",
                "status": "OPEN",
                "tags": ["mw-outbound-path-send-message"],
                "comments": [
                    {"type": "text", "is_operator": False},
                    {"type": "text", "isOperator": True, "source": "Agent"},
                ],
            }
        }

        class _Resp:
            status_code = 200
            dry_run = False

            def json(self) -> dict:
                return payload

        class _Exec:
            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp()

        result = _fetch_ticket_snapshot(
            cast(Any, _Exec()),
            "ticket-2",
            allow_network=True,
        )
        self.assertEqual(result.get("last_message_source"), "operator")
        self.assertTrue(result.get("operator_reply_present"))
        self.assertTrue(result.get("latest_comment_is_operator"))
        self.assertEqual(result.get("latest_comment_source"), "agent")
        self.assertEqual(result.get("operator_reply_count"), 1)

    def test_fetch_ticket_snapshot_missing_operator_flag(self) -> None:
        payload = {
            "ticket": {
                "id": "ticket-3",
                "status": "OPEN",
                "tags": [],
                "comments": [
                    {"type": "text", "body": "hello"},
                ],
            }
        }

        class _Resp:
            status_code = 200
            dry_run = False

            def json(self) -> dict:
                return payload

        class _Exec:
            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp()

        result = _fetch_ticket_snapshot(
            cast(Any, _Exec()),
            "ticket-3",
            allow_network=True,
        )
        self.assertEqual(result.get("last_message_source"), "unknown")
        self.assertIsNone(result.get("operator_reply_present"))

    def test_fetch_ticket_snapshot_includes_customer_identity(self) -> None:
        payload = {
            "ticket": {
                "id": "ticket-4",
                "status": "OPEN",
                "customer_profile": {
                    "email": "Person@Example.com",
                    "name": "Jane Doe",
                },
                "comments": [{"type": "text", "is_operator": False}],
            }
        }

        class _Resp:
            status_code = 200
            dry_run = False

            def json(self) -> dict:
                return payload

        class _Exec:
            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp()

        result = _fetch_ticket_snapshot(
            cast(Any, _Exec()),
            "ticket-4",
            allow_network=True,
        )
        self.assertEqual(result.get("customer_email"), "person@example.com")
        self.assertEqual(result.get("customer_name"), "jane doe")
        self.assertFalse(result.get("latest_comment_is_operator"))

    def test_fetch_ticket_snapshot_retries_on_rate_limit(self) -> None:
        payload = {
            "ticket": {
                "id": "ticket-rl",
                "status": "OPEN",
                "tags": [],
                "comments": [{"type": "text", "is_operator": False}],
            }
        }

        class _Exec:
            def __init__(self) -> None:
                self.calls = 0

            def execute(self, *args: Any, **kwargs: Any) -> Any:
                self.calls += 1
                if self.calls == 1:
                    response = RichpanelResponse(
                        status_code=429,
                        headers={},
                        body=b"{}",
                        url="https://example.com",
                        dry_run=False,
                    )
                    raise RichpanelRequestError("rate_limited", response=response)
                return RichpanelResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(payload).encode("utf-8"),
                    url="https://example.com",
                    dry_run=False,
                )

        executor = _Exec()
        result = _fetch_ticket_snapshot(
            cast(Any, executor),
            "ticket-rl",
            allow_network=True,
        )
        self.assertEqual(executor.calls, 2)
        self.assertEqual(result.get("status"), "OPEN")

    def test_fetch_latest_reply_body_handles_non_dict(self) -> None:
        class _Resp:
            def __init__(self, payload: Any) -> None:
                self._payload = payload

            def json(self) -> Any:
                return self._payload

        class _Exec:
            def __init__(self, payload: Any) -> None:
                self.payload = payload

            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp(self.payload)

        result = _fetch_latest_reply_body(
            cast(Any, _Exec(["not", "a", "dict"])),
            "ticket-4",
            allow_network=True,
        )
        self.assertIsNone(result)

        payload = {
            "comments": [
                {"is_operator": True, "body": "Reply body"},
            ]
        }
        result = _fetch_latest_reply_body(
            cast(Any, _Exec(payload)),
            "ticket-5",
            allow_network=True,
        )
        self.assertEqual(result, "Reply body")

    def test_fetch_ticket_snapshot_operator_reply(self) -> None:
        payload = {
            "ticket": {
                "id": "ticket-2",
                "status": "OPEN",
                "tags": [],
                "comments": [
                    {"type": "text", "is_operator": False},
                    {"type": "reply", "is_operator": True},
                ],
            }
        }

        class _Resp:
            status_code = 200
            dry_run = False

            def json(self) -> dict:
                return payload

        class _Exec:
            def execute(self, *args: Any, **kwargs: Any) -> _Resp:
                return _Resp()

        result = _fetch_ticket_snapshot(
            cast(Any, _Exec()),
            "ticket-2",
            allow_network=True,
        )
        self.assertTrue(result.get("operator_reply_present"))
        self.assertEqual(result.get("operator_reply_count"), 1)
        self.assertEqual(result.get("last_message_source"), "operator")

    def test_build_followup_payload_strips_force_primary(self) -> None:
        base = {
            "event_id": "evt:123",
            "scenario_name": "order_status",
            "intent": "order_status_tracking",
            "force_openai_routing_primary": True,
        }
        followup = _build_followup_payload(
            base, followup_message="ok", scenario_variant="order_status"
        )
        self.assertNotIn("force_openai_routing_primary", followup)


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

    def test_fail_reason_includes_operator_reply(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=False,
            status_resolved_ok=True,
            middleware_tag_ok=True,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=False,
            failed=["operator_reply_present"],
        )
        self.assertEqual(result, "FAIL")
        self.assertEqual(reason, "Failed criteria: operator_reply_present")

    def test_fail_reason_includes_send_message_tag(self) -> None:
        result, reason = _classify_order_status_result(
            base_pass=False,
            status_resolved_ok=True,
            middleware_tag_ok=True,
            middleware_ok=True,
            skip_tags_present_ok=True,
            auto_close_applied=False,
            fallback_used=False,
            failed=["send_message_tag_present"],
        )
        self.assertEqual(result, "FAIL")
        self.assertEqual(reason, "Failed criteria: send_message_tag_present")

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

    def test_pii_scan_detects_order_number_flag(self) -> None:
        payload = '{"command":"python scripts/dev_e2e_smoke.py --order-number 8123"}'
        self.assertIsNotNone(_check_pii_safe(payload))

    def test_pii_scan_allows_openai_response_id(self) -> None:
        payload = '{"openai":{"routing":{"response_id":"resp_abc123"}}}'
        self.assertIsNone(_check_pii_safe(payload))

    def test_redact_command_masks_sensitive_flags(self) -> None:
        cmd_parts = ["scripts/dev_e2e_smoke.py"]
        cmd_parts.extend(["--ticket-number", "1039"])
        cmd_parts.extend(["--event-id", "evt:ac89d31a"])
        cmd_parts.extend(["--ticket-from-email", "sandbox.test+autoticket@example.com"])
        cmd_parts.extend(["--ticket-subject", "Sandbox smoke"])
        cmd_parts.extend(["--ticket-body", "Automated smoke body"])
        cmd_parts.extend(["--order-number", "55555"])
        cmd_parts.extend(["--scenario", "order_status"])
        cmd = _redact_command(cmd_parts)
        self.assertIn("--ticket-number <redacted>", cmd)
        self.assertIn("--event-id <redacted>", cmd)
        self.assertIn("--ticket-from-email <redacted>", cmd)
        self.assertIn("--ticket-subject <redacted>", cmd)
        self.assertIn("--ticket-body <redacted>", cmd)
        self.assertIn("--order-number <redacted>", cmd)
        self.assertNotIn("1039", cmd)
        self.assertNotIn("evt:ac89d31a", cmd)
        self.assertNotIn("sandbox.test+autoticket@example.com", cmd)
        self.assertNotIn("Sandbox smoke", cmd)
        self.assertNotIn("Automated smoke body", cmd)
        self.assertNotIn("55555", cmd)
        self.assertTrue(cmd.startswith("python "))


class OrderNumberResolutionTests(unittest.TestCase):
    def test_resolve_order_number_prefers_arg(self) -> None:
        with patch.dict(os.environ, {"MW_SMOKE_ORDER_NUMBER": "111"}, clear=True):
            self.assertEqual(_resolve_order_number(" #987 "), "987")

    def test_resolve_order_number_env(self) -> None:
        with patch.dict(os.environ, {"MW_SMOKE_ORDER_NUMBER": " 456 "}, clear=True):
            self.assertEqual(_resolve_order_number(None), "456")

    def test_resolve_order_number_missing_candidate(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_resolve_order_number(""))

    def test_resolve_order_number_empty_candidate(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_resolve_order_number("   "))

    def test_resolve_order_number_str_failure(self) -> None:
        class _BadValue:
            def __str__(self) -> str:
                raise RuntimeError("boom")

        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_resolve_order_number(_BadValue()))  # type: ignore[arg-type]

    def test_fetch_recent_shopify_order_number_success(self) -> None:
        class _Resp:
            def __init__(self) -> None:
                self.status_code = 200
                self.dry_run = False

            def json(self) -> dict:
                return {"orders": [{"order_number": "12345"}]}

        class _Client:
            def request(self, *_args: Any, **_kwargs: Any) -> _Resp:
                return _Resp()

        with patch("dev_e2e_smoke.ShopifyClient", return_value=_Client()):
            value = _fetch_recent_shopify_order_number(
                allow_network=True, safe_mode=False, automation_enabled=True
            )
        self.assertEqual(value, "12345")

    def test_fetch_recent_shopify_order_number_name_fallback(self) -> None:
        class _Resp:
            def __init__(self) -> None:
                self.status_code = 200
                self.dry_run = False

            def json(self) -> dict:
                return {"orders": [{"name": "#9999"}]}

        class _Client:
            def request(self, *_args: Any, **_kwargs: Any) -> _Resp:
                return _Resp()

        with patch("dev_e2e_smoke.ShopifyClient", return_value=_Client()):
            value = _fetch_recent_shopify_order_number(
                allow_network=True, safe_mode=False, automation_enabled=True
            )
        self.assertEqual(value, "9999")

    def test_fetch_recent_shopify_order_number_no_orders(self) -> None:
        class _Resp:
            def __init__(self) -> None:
                self.status_code = 200
                self.dry_run = False

            def json(self) -> dict:
                return {"orders": []}

        class _Client:
            def request(self, *_args: Any, **_kwargs: Any) -> _Resp:
                return _Resp()

        with patch("dev_e2e_smoke.ShopifyClient", return_value=_Client()):
            value = _fetch_recent_shopify_order_number(
                allow_network=True, safe_mode=False, automation_enabled=True
            )
        self.assertIsNone(value)

    def test_fetch_recent_shopify_order_number_dry_run(self) -> None:
        class _Resp:
            def __init__(self) -> None:
                self.status_code = 200
                self.dry_run = True

            def json(self) -> dict:
                return {"orders": [{"order_number": "12345"}]}

        class _Client:
            def request(self, *_args: Any, **_kwargs: Any) -> _Resp:
                return _Resp()

        with patch("dev_e2e_smoke.ShopifyClient", return_value=_Client()):
            value = _fetch_recent_shopify_order_number(
                allow_network=True, safe_mode=False, automation_enabled=True
            )
        self.assertIsNone(value)
        self.assertEqual(_Resp().json(), {"orders": [{"order_number": "12345"}]})

    def test_fetch_recent_shopify_order_number_exception(self) -> None:
        class _Client:
            def request(self, *_args: Any, **_kwargs: Any) -> None:
                raise RuntimeError("boom")

        with patch("dev_e2e_smoke.ShopifyClient", return_value=_Client()):
            value = _fetch_recent_shopify_order_number(
                allow_network=True, safe_mode=False, automation_enabled=True
            )
        self.assertIsNone(value)

    def test_fetch_recent_shopify_order_number_skips_when_disabled(self) -> None:
        value = _fetch_recent_shopify_order_number(
            allow_network=False, safe_mode=False, automation_enabled=True
        )
        self.assertIsNone(value)


class AutoTicketHelpersTests(unittest.TestCase):
    def test_resolve_smoke_ticket_text_defaults_and_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                _resolve_smoke_ticket_text(
                    None, env_key="MW_SMOKE_TICKET_BODY", default="default"
                ),
                "default",
            )
            self.assertEqual(
                _resolve_smoke_ticket_text(
                    "  hello  ",
                    env_key="MW_SMOKE_TICKET_BODY",
                    default="default",
                ),
                "hello",
            )
        with patch.dict(
            os.environ, {"MW_SMOKE_TICKET_BODY": "  env  "}, clear=True
        ):
            self.assertEqual(
                _resolve_smoke_ticket_text(
                    None, env_key="MW_SMOKE_TICKET_BODY", default="default"
                ),
                "env",
            )

    def test_redact_identifier(self) -> None:
        self.assertIsNone(_redact_identifier(None))
        redacted = _redact_identifier("ticket-123")
        self.assertTrue(redacted.startswith("redacted:"))
        self.assertNotIn("ticket-123", redacted)

    def test_extract_created_ticket_fields(self) -> None:
        number, ticket_id = _extract_created_ticket_fields(
            {"ticket": {"conversation_no": 123, "id": "t-1"}}
        )
        self.assertEqual(number, "123")
        self.assertEqual(ticket_id, "t-1")
        number, ticket_id = _extract_created_ticket_fields(
            {"conversation_number": "456", "ticket_id": "t-2"}
        )
        self.assertEqual(number, "456")
        self.assertEqual(ticket_id, "t-2")

    def test_build_create_ticket_payload_shape(self) -> None:
        payload = _build_create_ticket_payload(
            from_email="from@example.com",
            to_email="support@example.com",
            subject="Subject",
            body="Body",
            first_name="Sandbox",
            last_name="Test",
        )
        ticket = payload["ticket"]
        self.assertEqual(ticket["comment"]["public"], True)
        self.assertEqual(
            ticket["via"]["source"]["from"]["address"], "from@example.com"
        )
        self.assertEqual(
            ticket["via"]["source"]["to"]["address"], "support@example.com"
        )
        self.assertEqual(ticket["customer_profile"]["firstName"], "Sandbox")
        self.assertEqual(ticket["customer_profile"]["lastName"], "Test")
        self.assertEqual(ticket["tags"], _SMOKE_TICKET_TAGS)

    def test_create_ticket_prod_requires_ack(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch(
            "dev_e2e_smoke.RichpanelClient"
        ):
            with self.assertRaises(SmokeFailure):
                _create_sandbox_email_ticket(
                    env_name="prod",
                    region="us-east-2",
                    stack_name="RichpanelMiddleware-prod",
                    api_key_secret_id=None,
                    from_email="from@example.com",
                    to_email="support@example.com",
                    subject="Subject",
                    body="Body",
                    first_name="Sandbox",
                    last_name="Test",
                    proof_path=None,
                    prod_writes_ack=None,
                )

    def test_create_ticket_prod_ack_allows(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"ticket": {"conversation_no": 321, "id": "t-1"}}

        class _StubClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _StubResponse:
                return _StubResponse()

        with patch("dev_e2e_smoke.RichpanelClient", _StubClient):
            result = _create_sandbox_email_ticket(
                env_name="prod",
                region="us-east-2",
                stack_name="RichpanelMiddleware-prod",
                api_key_secret_id=None,
                from_email="from@example.com",
                to_email="support@example.com",
                subject="Subject",
                body="Body",
                first_name="Sandbox",
                last_name="Test",
                proof_path=None,
                prod_writes_ack="I_UNDERSTAND_PROD_WRITES",
            )
            self.assertEqual(result["ticket_number"], "321")

    def test_create_ticket_script_prod_requires_ack(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                _require_prod_write_ack_script(env_name="prod", ack_token=None)

    def test_create_ticket_script_prod_ack_allows(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            _require_prod_write_ack_script(
                env_name="production", ack_token="I_UNDERSTAND_PROD_WRITES"
            )


class ChatTicketHelpersTests(unittest.TestCase):
    def test_build_chat_ticket_payload_omits_source_for_non_email(self) -> None:
        payload = _build_chat_ticket_payload(
            channel="chat",
            from_email="from@example.com",
            to_email="support@example.com",
            subject="Subject",
            body="Body",
            first_name="Sandbox",
            last_name="Test",
        )
        ticket = payload["ticket"]
        self.assertEqual(ticket["via"]["channel"], "chat")
        self.assertNotIn("source", ticket["via"])

    def test_build_chat_ticket_payload_includes_source_for_email(self) -> None:
        payload = _build_chat_ticket_payload(
            channel="email",
            from_email="from@example.com",
            to_email="support@example.com",
            subject="Subject",
            body="Body",
            first_name="Sandbox",
            last_name="Test",
        )
        ticket = payload["ticket"]
        self.assertEqual(
            ticket["via"]["source"]["from"]["address"], "from@example.com"
        )
        self.assertEqual(ticket["via"]["source"]["to"]["address"], "support@example.com")

    def test_chat_redact_emails_masks_addresses(self) -> None:
        redacted = _chat_redact_emails(
            "contact us at support@example.com or test+1@demo.co"
        )
        self.assertNotIn("support@example.com", redacted)
        self.assertNotIn("test+1@demo.co", redacted)
        self.assertIn("<redacted-email>", redacted)

    def test_chat_extract_ticket_fields(self) -> None:
        ticket_number, ticket_id = _extract_chat_ticket_fields(
            {"ticket": {"conversation_no": 123, "id": "t-1"}}
        )
        self.assertEqual(ticket_number, "123")
        self.assertEqual(ticket_id, "t-1")

    def test_chat_require_prod_write_ack_blocks(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                _require_prod_write_ack_chat(env_name="prod", ack_token=None)

    def test_chat_ticket_main_requires_boto3(self) -> None:
        with patch.object(sys, "argv", ["create_sandbox_chat_ticket.py", "--env", "dev", "--region", "us-east-2"]):
            with patch("create_sandbox_chat_ticket.boto3", None):
                self.assertEqual(_chat_ticket_main(), 1)

    def test_chat_ticket_main_success(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"ticket": {"conversation_no": 123, "id": "t-1"}}

        class _StubClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _StubResponse:
                return _StubResponse()

        class _StubBoto3:
            def setup_default_session(self, **_: Any) -> None:
                return None

        with TemporaryDirectory() as tmp_dir:
            proof_path = str(Path(tmp_dir) / "created_chat_ticket.json")
            argv = [
                "create_sandbox_chat_ticket.py",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--proof-path",
                proof_path,
            ]
            with patch.object(sys, "argv", argv):
                with patch("create_sandbox_chat_ticket.boto3", _StubBoto3()):
                    with patch("create_sandbox_chat_ticket.RichpanelClient", _StubClient):
                        result = _chat_ticket_main()
            self.assertEqual(result, 0)
            self.assertTrue(Path(proof_path).exists())

    def test_chat_ticket_main_dry_run_fails(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = True
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"ticket": {"conversation_no": 123, "id": "t-1"}}

        class _StubClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _StubResponse:
                return _StubResponse()

        class _StubBoto3:
            def setup_default_session(self, **_: Any) -> None:
                return None

        argv = ["create_sandbox_chat_ticket.py", "--env", "dev", "--region", "us-east-2"]
        with patch.object(sys, "argv", argv):
            with patch("create_sandbox_chat_ticket.boto3", _StubBoto3()):
                with patch("create_sandbox_chat_ticket.RichpanelClient", _StubClient):
                    self.assertEqual(_chat_ticket_main(), 1)
        self.assertEqual(
            _StubResponse().json(), {"ticket": {"conversation_no": 123, "id": "t-1"}}
        )

    def test_chat_ticket_main_http_error(self) -> None:
        class _StubResponse:
            status_code = 400
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"error": "Invalid value for support@example.com"}

        class _StubClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _StubResponse:
                return _StubResponse()

        class _StubBoto3:
            def setup_default_session(self, **_: Any) -> None:
                return None

        argv = ["create_sandbox_chat_ticket.py", "--env", "dev", "--region", "us-east-2"]
        with patch.object(sys, "argv", argv):
            with patch("create_sandbox_chat_ticket.boto3", _StubBoto3()):
                with patch("create_sandbox_chat_ticket.RichpanelClient", _StubClient):
                    self.assertEqual(_chat_ticket_main(), 1)

    def test_chat_ticket_main_missing_identifiers(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"ticket": {}}

        class _StubClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _StubResponse:
                return _StubResponse()

        class _StubBoto3:
            def setup_default_session(self, **_: Any) -> None:
                return None

        argv = ["create_sandbox_chat_ticket.py", "--env", "dev", "--region", "us-east-2"]
        with patch.object(sys, "argv", argv):
            with patch("create_sandbox_chat_ticket.boto3", _StubBoto3()):
                with patch("create_sandbox_chat_ticket.RichpanelClient", _StubClient):
                    self.assertEqual(_chat_ticket_main(), 1)

    def test_create_ticket_script_prod_ack_from_env_allows(self) -> None:
        with patch.dict(
            os.environ, {"MW_PROD_WRITES_ACK": "I_UNDERSTAND_PROD_WRITES"}, clear=True
        ):
            _require_prod_write_ack_script(env_name="prod", ack_token=None)

    def test_create_ticket_script_non_prod_allows(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            _require_prod_write_ack_script(env_name="dev", ack_token=None)

    def test_create_sandbox_email_ticket_success(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"ticket": {"conversation_no": 321, "id": "t-1"}}

        class _StubClient:
            last_instance = None

            def __init__(self, **_: Any) -> None:
                _StubClient.last_instance = self
                self.calls: list[tuple[str, str, dict]] = []

            def request(self, method: str, path: str, **kwargs: Any) -> _StubResponse:
                self.calls.append((method, path, kwargs))
                return _StubResponse()

        with TemporaryDirectory() as tmpdir, patch(
            "dev_e2e_smoke.RichpanelClient", _StubClient
        ):
            proof_path = Path(tmpdir) / "created.json"
            result = _create_sandbox_email_ticket(
                env_name="dev",
                region="us-east-2",
                stack_name="RichpanelMiddleware-dev",
                api_key_secret_id=None,
                from_email="from@example.com",
                to_email="support@example.com",
                subject="Subject",
                body="Body",
                first_name="Sandbox",
                last_name="Test",
                proof_path=proof_path,
            )
            self.assertEqual(result["ticket_number"], "321")
            self.assertEqual(result["ticket_id"], "t-1")
            self.assertTrue(proof_path.exists())
            artifact = json.loads(proof_path.read_text(encoding="utf-8"))
            self.assertEqual(
                artifact["response"]["ticket_number_fingerprint"],
                result["ticket_number_fingerprint"],
            )
            self.assertEqual(
                artifact["response"]["conversation_id_fingerprint"],
                result["ticket_id_fingerprint"],
            )
            self.assertTrue(
                artifact["response"]["ticket_number_redacted"].startswith("redacted:")
            )
            self.assertEqual(artifact["request"]["channel"], "email")
            self.assertEqual(_StubClient.last_instance.calls[0][1], "/v1/tickets")

    def test_create_sandbox_email_ticket_dry_run_fails(self) -> None:
        class _DryRunResponse:
            status_code = 200
            dry_run = True
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {}

        class _DryRunClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _DryRunResponse:
                return _DryRunResponse()

        with patch("dev_e2e_smoke.RichpanelClient", _DryRunClient):
            self.assertEqual(_DryRunResponse().json(), {})
            with self.assertRaises(SmokeFailure):
                _create_sandbox_email_ticket(
                    env_name="dev",
                    region="us-east-2",
                    stack_name="RichpanelMiddleware-dev",
                    api_key_secret_id=None,
                    from_email="from@example.com",
                    to_email="support@example.com",
                    subject="Subject",
                    body="Body",
                    first_name="Sandbox",
                    last_name="Test",
                    proof_path=None,
                )

    def test_create_sandbox_email_ticket_http_error_fails(self) -> None:
        class _ErrorResponse:
            status_code = 500
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                return {"error": "boom"}

        class _ErrorClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _ErrorResponse:
                return _ErrorResponse()

        with patch("dev_e2e_smoke.RichpanelClient", _ErrorClient):
            with self.assertRaises(SmokeFailure):
                _create_sandbox_email_ticket(
                    env_name="dev",
                    region="us-east-2",
                    stack_name="RichpanelMiddleware-dev",
                    api_key_secret_id=None,
                    from_email="from@example.com",
                    to_email="support@example.com",
                    subject="Subject",
                    body="Body",
                    first_name="Sandbox",
                    last_name="Test",
                    proof_path=None,
                )

    def test_create_sandbox_email_ticket_non_json_error(self) -> None:
        class _ErrorResponse:
            status_code = 500
            dry_run = False
            url = "https://api.richpanel.com/v1/tickets"

            def json(self) -> dict:
                raise ValueError("not json")

        class _ErrorClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> _ErrorResponse:
                return _ErrorResponse()

        with patch("dev_e2e_smoke.RichpanelClient", _ErrorClient):
            with self.assertRaises(SmokeFailure):
                _create_sandbox_email_ticket(
                    env_name="dev",
                    region="us-east-2",
                    stack_name="RichpanelMiddleware-dev",
                    api_key_secret_id=None,
                    from_email="from@example.com",
                    to_email="support@example.com",
                    subject="Subject",
                    body="Body",
                    first_name="Sandbox",
                    last_name="Test",
                    proof_path=None,
                )

    def test_create_sandbox_email_ticket_write_disabled(self) -> None:
        class _WriteDisabledClient:
            def __init__(self, **_: Any) -> None:
                pass

            def request(self, *_: Any, **__: Any) -> None:
                raise RichpanelWriteDisabledError("writes disabled")

        with patch("dev_e2e_smoke.RichpanelClient", _WriteDisabledClient):
            with self.assertRaises(SmokeFailure):
                _create_sandbox_email_ticket(
                    env_name="dev",
                    region="us-east-2",
                    stack_name="RichpanelMiddleware-dev",
                    api_key_secret_id=None,
                    from_email="from@example.com",
                    to_email="support@example.com",
                    subject="Subject",
                    body="Body",
                    first_name="Sandbox",
                    last_name="Test",
                    proof_path=None,
                )

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


class RedactionHelpersTests(unittest.TestCase):
    def test_redact_path_number_endpoint(self) -> None:
        path = "/v1/tickets/number/12345"
        self.assertEqual(_redact_path(path), "/v1/tickets/number/<redacted>")
        self.assertEqual(_extract_endpoint_variant(path), "number")

    def test_redact_path_id_with_suffix(self) -> None:
        path = "/v1/tickets/abc123/add-tags"
        self.assertEqual(_redact_path(path), "/v1/tickets/<redacted>/add-tags")
        self.assertEqual(_extract_endpoint_variant(path), "id")

    def test_redact_path_unknown(self) -> None:
        self.assertEqual(_redact_path("/v2/other"), "<redacted>")
        self.assertEqual(_extract_endpoint_variant("/v2/other"), "unknown")

    def test_sanitize_ticket_snapshot_fingerprints(self) -> None:
        snapshot = {
            "ticket_id": "TICKET-123",
            "path": "/v1/tickets/abc123",
            "customer_email": "person@example.com",
            "customer_name": "Jane Doe",
        }
        sanitized = _sanitize_ticket_snapshot(snapshot)
        self.assertIsNotNone(sanitized)
        self.assertNotIn("ticket_id", sanitized)
        self.assertIn("ticket_id_fingerprint", sanitized)
        self.assertEqual(sanitized.get("endpoint_variant"), "id")
        self.assertEqual(sanitized.get("path_redacted"), "/v1/tickets/<redacted>")
        self.assertIn("customer_email_fingerprint", sanitized)
        self.assertIn("customer_name_fingerprint", sanitized)

    def test_sanitize_tag_result_redacts_path(self) -> None:
        tag_result = {"path": "/v1/tickets/abc123/add-tags", "status": "ok"}
        sanitized = _sanitize_tag_result(tag_result)
        self.assertEqual(
            sanitized.get("path_redacted"), "/v1/tickets/<redacted>/add-tags"
        )


class SeedOrderIdTests(unittest.TestCase):
    def test_seed_order_id_uses_conversation_id(self) -> None:
        seeded = _seed_order_id("RUN1", "conv-123")
        self.assertTrue(seeded.startswith("ORDER-"))
        self.assertNotIn("conv-123", seeded)

    def test_seed_order_id_falls_back_to_run_id(self) -> None:
        seeded = _seed_order_id("RUN2", None)
        self.assertTrue(seeded.startswith("DEV-ORDER-"))


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


class OpenAIEvidenceTests(unittest.TestCase):
    def test_openai_routing_evidence_maps_response_id(self) -> None:
        state_item = {
            "routing_artifact": {
                "primary_source": "deterministic",
                "llm_suggestion": {
                    "llm_called": True,
                    "model": "gpt-5.2-chat-latest",
                    "confidence": 0.91,
                    "response_id": "resp_123",
                },
            }
        }
        evidence = _extract_openai_routing_evidence(
            state_item, {}, routing_intent="order_status_tracking"
        )
        self.assertTrue(evidence["llm_called"])
        self.assertEqual(evidence["model"], "gpt-5.2-chat-latest")
        self.assertEqual(evidence["response_id"], "resp_123")
        self.assertEqual(evidence["final_intent"], "order_status_tracking")
        self.assertEqual(evidence["final_source"], "deterministic")

    def test_openai_routing_evidence_missing_response_id(self) -> None:
        state_item = {
            "routing_artifact": {
                "llm_suggestion": {
                    "llm_called": True,
                    "model": "gpt-5.2-chat-latest",
                    "confidence": 0.42,
                }
            }
        }
        evidence = _extract_openai_routing_evidence(
            state_item, {}, routing_intent="order_status_tracking"
        )
        self.assertIsNone(evidence["response_id"])
        self.assertEqual(evidence["response_id_unavailable_reason"], "response_id_missing")

    def test_openai_rewrite_evidence_disabled(self) -> None:
        state_item = {
            "openai_rewrite": {
                "rewrite_attempted": False,
                "rewrite_applied": False,
                "model": "gpt-5.2-chat-latest",
                "response_id": None,
                "response_id_unavailable_reason": "rewrite_disabled",
                "fallback_used": False,
                "reason": "rewrite_disabled",
                "error_class": None,
            }
        }
        evidence = _extract_openai_rewrite_evidence(state_item, {})
        self.assertFalse(evidence["rewrite_attempted"])
        self.assertEqual(evidence["reason"], "disabled")
        self.assertIsNone(evidence["original_hash"])
        self.assertIsNone(evidence["rewritten_hash"])

    def test_openai_intent_evidence_maps_response_id(self) -> None:
        state_item = {
            "order_status_intent": {
                "llm_called": True,
                "model": "gpt-5.2-chat-latest",
                "response_id": "resp_intent",
                "confidence_threshold": 0.85,
                "accepted": True,
                "ticket_excerpt_redacted": "<redacted>",
                "result": {
                    "is_order_status": True,
                    "confidence": 0.9,
                    "extracted_order_number": "12345",
                    "language": "en",
                },
            }
        }
        evidence = _extract_order_status_intent_evidence(state_item, {})
        self.assertTrue(evidence["llm_called"])
        self.assertEqual(evidence["response_id"], "resp_intent")
        self.assertEqual(evidence["confidence"], 0.9)
        self.assertEqual(evidence["is_order_status"], True)
        self.assertEqual(evidence["language"], "en")
        self.assertTrue(str(evidence["extracted_order_number_redacted"]).startswith("redacted:"))

    def test_openai_requirements_fail_when_missing(self) -> None:
        routing = {"llm_called": False}
        rewrite = {"rewrite_attempted": False, "rewrite_applied": False}
        result = _evaluate_openai_requirements(
            routing,
            rewrite,
            require_routing=True,
            require_rewrite=True,
        )
        self.assertFalse(result["openai_routing_called"])
        self.assertFalse(result["openai_routing_source_openai"])
        self.assertFalse(result["openai_rewrite_attempted"])
        self.assertFalse(result["openai_rewrite_applied"])

    def test_openai_requirements_accept_fallback(self) -> None:
        routing = {"llm_called": True, "final_source": "openai"}
        rewrite = {
            "rewrite_attempted": True,
            "rewrite_applied": False,
            "fallback_used": True,
        }
        result = _evaluate_openai_requirements(
            routing,
            rewrite,
            require_routing=True,
            require_rewrite=True,
        )
        self.assertTrue(result["openai_routing_called"])
        self.assertTrue(result["openai_routing_source_openai"])
        self.assertTrue(result["openai_rewrite_attempted"])
        self.assertTrue(result["openai_rewrite_applied"])

    def test_openai_evidence_contains_required_fields(self) -> None:
        state_item = {
            "routing_artifact": {
                "llm_suggestion": {
                    "llm_called": True,
                    "model": "gpt-5.2-chat-latest",
                    "confidence": 0.88,
                    "response_id": "resp_abc",
                }
            },
            "openai_rewrite": {
                "rewrite_attempted": True,
                "rewrite_applied": True,
                "model": "gpt-5.2-chat-latest",
                "response_id": "resp_xyz",
                "response_id_unavailable_reason": None,
                "fallback_used": False,
                "reason": "applied",
                "error_class": None,
            },
        }
        routing = _extract_openai_routing_evidence(
            state_item, {}, routing_intent="order_status_tracking"
        )
        rewrite = _extract_openai_rewrite_evidence(state_item, {})
        for key in (
            "llm_called",
            "model",
            "confidence",
            "response_id",
            "final_intent",
            "final_source",
        ):
            self.assertIn(key, routing)
        for key in (
            "rewrite_attempted",
            "rewrite_applied",
            "model",
            "response_id",
            "fallback_used",
            "original_hash",
            "rewritten_hash",
            "rewritten_changed",
        ):
            self.assertIn(key, rewrite)


class WaitForTicketReadyTests(unittest.TestCase):
    def test_wait_for_ticket_ready_returns_snapshot(self) -> None:
        snapshots = [
            {"status": "open", "tags": []},
            {"status": "closed", "tags": ["mw-auto-replied"]},
        ]
        with patch(
            "dev_e2e_smoke._fetch_ticket_snapshot", side_effect=snapshots
        ) as fetch_mock:
            result = _wait_for_ticket_ready(
                MagicMock(),
                "conv-1",
                allow_network=True,
                required_tags=["mw-auto-replied"],
                required_statuses=["resolved", "closed"],
                timeout_seconds=5,
                poll_interval=0.0,
            )

        self.assertEqual(fetch_mock.call_count, 2)
        self.assertEqual(result, snapshots[-1])

    def test_wait_for_ticket_ready_times_out(self) -> None:
        with patch(
            "dev_e2e_smoke._fetch_ticket_snapshot",
            return_value={"status": "open", "tags": []},
        ):
            result = _wait_for_ticket_ready(
                MagicMock(),
                "conv-2",
                allow_network=True,
                required_tags=["mw-auto-replied"],
                required_statuses=["resolved", "closed"],
                timeout_seconds=0,
                poll_interval=0.0,
            )

        self.assertIsNone(result)


class WaitForTicketTagsTests(unittest.TestCase):
    def test_wait_for_ticket_tags_returns_snapshot(self) -> None:
        snapshots = [
            {"tags": []},
            {"tags": ["mw-outbound-blocked-allowlist"]},
        ]
        with patch(
            "dev_e2e_smoke._fetch_ticket_snapshot", side_effect=snapshots
        ) as fetch_mock:
            result = _wait_for_ticket_tags(
                MagicMock(),
                "conv-3",
                allow_network=True,
                required_tags=["mw-outbound-blocked-allowlist"],
                timeout_seconds=5,
                poll_interval=0.0,
            )

        self.assertEqual(fetch_mock.call_count, 2)
        self.assertEqual(result, snapshots[-1])

    def test_wait_for_ticket_tags_times_out(self) -> None:
        with patch(
            "dev_e2e_smoke._fetch_ticket_snapshot",
            return_value={"tags": []},
        ):
            result = _wait_for_ticket_tags(
                MagicMock(),
                "conv-4",
                allow_network=True,
                required_tags=["mw-outbound-blocked-allowlist"],
                timeout_seconds=0,
                poll_interval=0.0,
            )

        self.assertIsNone(result)


class OpenAIRewriteWaitTests(unittest.TestCase):
    def test_wait_for_openai_rewrite_state_record(self) -> None:
        table = MagicMock()
        table.get_item.return_value = {
            "Item": {"openai_rewrite": {"rewrite_attempted": True}}
        }
        ddb = MagicMock()
        ddb.Table.return_value = table

        with patch("dev_e2e_smoke.time.sleep"):
            item = wait_for_openai_rewrite_state_record(
                ddb,
                table_name="state-table",
                conversation_id="conv-1",
                timeout_seconds=1,
                poll_interval=0,
            )
        self.assertIn("openai_rewrite", item)
        self.assertTrue(item["openai_rewrite"]["rewrite_attempted"])

    def test_wait_for_openai_rewrite_audit_record(self) -> None:
        class _FakeKey:
            def __init__(self, name: str) -> None:
                self.name = name

            def eq(self, value: str) -> dict[str, str]:
                return {"name": self.name, "value": value}

        table = MagicMock()
        table.query.return_value = {
            "Items": [
                {
                    "event_id": "evt-1",
                    "openai_rewrite": {"rewrite_attempted": True},
                }
            ]
        }
        ddb = MagicMock()
        ddb.Table.return_value = table

        with patch("dev_e2e_smoke.time.sleep"), patch("dev_e2e_smoke.Key", _FakeKey):
            item = wait_for_openai_rewrite_audit_record(
                ddb,
                table_name="audit-table",
                conversation_id="conv-1",
                event_id="evt-1",
                timeout_seconds=1,
                poll_interval=0,
            )
        self.assertIn("openai_rewrite", item)
        self.assertTrue(item["openai_rewrite"]["rewrite_attempted"])


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


def _build_suite(loader: unittest.TestLoader) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ScenarioPayloadTests))
    suite.addTests(loader.loadTestsFromTestCase(PayloadBuilderTests))
    suite.addTests(loader.loadTestsFromTestCase(ParseArgsTests))
    suite.addTests(loader.loadTestsFromTestCase(TestRequirementFlagResolution))
    suite.addTests(loader.loadTestsFromTestCase(RoutingValidationTests))
    suite.addTests(loader.loadTestsFromTestCase(URLEncodingTests))
    suite.addTests(loader.loadTestsFromTestCase(DraftReplyHelperTests))
    suite.addTests(loader.loadTestsFromTestCase(DiagnosticsTests))
    suite.addTests(loader.loadTestsFromTestCase(ReplyEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(CriteriaTests))
    suite.addTests(loader.loadTestsFromTestCase(OutboundEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(OutboundAttemptedTests))
    suite.addTests(loader.loadTestsFromTestCase(OutboundFailureClassificationTests))
    suite.addTests(loader.loadTestsFromTestCase(SendMessageStatusTests))
    suite.addTests(loader.loadTestsFromTestCase(OperatorReplyEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(SendMessageEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(AllowlistEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(SupportRoutingTests))
    suite.addTests(loader.loadTestsFromTestCase(OrderMatchEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(OrderMatchResolutionTests))
    suite.addTests(loader.loadTestsFromTestCase(ReplyContentFlagsTests))
    suite.addTests(loader.loadTestsFromTestCase(OrderNumberResolutionTests))
    suite.addTests(loader.loadTestsFromTestCase(AllowlistSkipTests))
    suite.addTests(loader.loadTestsFromTestCase(SkipProofPayloadTests))
    suite.addTests(loader.loadTestsFromTestCase(AllowlistConfigTests))
    suite.addTests(loader.loadTestsFromTestCase(ProofPayloadWriteTests))
    suite.addTests(loader.loadTestsFromTestCase(OperatorSendMessageHelperTests))
    suite.addTests(loader.loadTestsFromTestCase(OutboundResultHelperTests))
    suite.addTests(loader.loadTestsFromTestCase(TicketSnapshotTests))
    suite.addTests(loader.loadTestsFromTestCase(ClassificationTests))
    suite.addTests(loader.loadTestsFromTestCase(PIISafetyTests))
    suite.addTests(loader.loadTestsFromTestCase(AutoTicketHelpersTests))
    suite.addTests(loader.loadTestsFromTestCase(ChatTicketHelpersTests))
    suite.addTests(loader.loadTestsFromTestCase(FollowupProofTests))
    suite.addTests(loader.loadTestsFromTestCase(RedactionHelpersTests))
    suite.addTests(loader.loadTestsFromTestCase(SeedOrderIdTests))
    suite.addTests(loader.loadTestsFromTestCase(SummaryAppendTests))
    suite.addTests(loader.loadTestsFromTestCase(OpenAIEvidenceTests))
    suite.addTests(loader.loadTestsFromTestCase(WaitForTicketReadyTests))
    suite.addTests(loader.loadTestsFromTestCase(WaitForTicketTagsTests))
    suite.addTests(loader.loadTestsFromTestCase(OpenAIRewriteWaitTests))
    suite.addTests(loader.loadTestsFromTestCase(FallbackCloseTests))
    return suite


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    return _build_suite(loader)


def main() -> int:  # pragma: no cover - CLI entrypoint
    loader = unittest.TestLoader()
    suite = _build_suite(loader)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
