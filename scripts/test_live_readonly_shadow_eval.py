from __future__ import annotations

import json
import os
import sys
import importlib
import unittest
import types
import hashlib
import io
import contextlib
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import live_readonly_shadow_eval as shadow_eval  # noqa: E402
import readonly_shadow_utils as shadow_utils  # noqa: E402


OPENAI_SHADOW_ENV = {
    "MW_OPENAI_ROUTING_ENABLED": "true",
    "MW_OPENAI_INTENT_ENABLED": "true",
    "MW_OPENAI_SHADOW_ENABLED": "true",
    "OPENAI_ALLOW_NETWORK": "true",
}


def _with_openai_env(env: dict) -> dict:
    merged = dict(OPENAI_SHADOW_ENV)
    merged.update(env)
    return merged


class _StubResponse:
    def __init__(self, payload: dict, status_code: int = 200, dry_run: bool = False):
        self.status_code = status_code
        self.dry_run = dry_run
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _StubClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, path: str, **kwargs) -> _StubResponse:
        self.requests.append((method, path))
        if path.startswith("/v1/tickets/"):
            payload = {
                "ticket": {
                    "id": "t-123",
                    "conversation_id": "conv-123",
                    "order": {"order_id": "order-123", "tracking_number": "TN123"},
                    "customer": {"email": "customer@example.com", "name": "Test User"},
                }
            }
            return _StubResponse(payload)
        if path.startswith("/api/v1/conversations/") or path.startswith(
            "/v1/conversations/"
        ):
            payload = {"customer_profile": {"phone": "555-1212"}}
            return _StubResponse(payload)
        return _StubResponse({}, status_code=404)


class _ListingClient:
    def __init__(self, list_payload: dict, *, status_code: int = 200):
        self.list_payload = list_payload
        self.status_code = status_code

    def request(self, method: str, path: str, **kwargs) -> _StubResponse:
        if path == "/v1/tickets":
            return _StubResponse(self.list_payload, status_code=self.status_code)
        return _StubResponse({}, status_code=404)


class _FallbackListingClient:
    def __init__(self, list_payload: dict):
        self.list_payload = list_payload
        self.paths: list[str] = []

    def request(self, method: str, path: str, **kwargs) -> _StubResponse:
        self.paths.append(path)
        if path == "/v1/tickets":
            return _StubResponse({}, status_code=403)
        if path == "/api/v1/conversations":
            return _StubResponse({}, status_code=404)
        if path == "/v1/conversations":
            return _StubResponse(self.list_payload, status_code=200)
        return _StubResponse({}, status_code=404)


class LiveReadonlyShadowEvalGuardTests(unittest.TestCase):
    def test_prod_requires_write_disabled(self) -> None:
        env = {
            "MW_ENV": "prod",
            "SHOPIFY_SHOP_DOMAIN": "test-shop.myshopify.com",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "false",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "123"]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as ctx:
                    shadow_eval.main()
        self.assertIn("RICHPANEL_WRITE_DISABLED", str(ctx.exception))


class LiveReadonlyShadowEvalB61CTests(unittest.TestCase):
    """Tests for B61/C diagnostic functions."""

    def test_extract_match_method_order_number(self) -> None:
        result = {
            "order_matched": True,
            "order_resolution": {"resolvedBy": "richpanel_order_number"},
        }
        method = shadow_eval._extract_match_method(result)
        self.assertEqual(method, "order_number")

    def test_extract_match_method_name_email(self) -> None:
        result = {
            "order_matched": True,
            "order_resolution": {"resolvedBy": "shopify_email_name"},
        }
        method = shadow_eval._extract_match_method(result)
        self.assertEqual(method, "name_email")

    def test_extract_match_method_email_only(self) -> None:
        result = {
            "order_matched": True,
            "order_resolution": {"resolvedBy": "shopify_email_only"},
        }
        method = shadow_eval._extract_match_method(result)
        self.assertEqual(method, "email_only")

    def test_extract_match_method_none(self) -> None:
        result = {
            "order_matched": False,
            "order_resolution": {"resolvedBy": "no_match"},
        }
        method = shadow_eval._extract_match_method(result)
        self.assertEqual(method, "none")

    def test_extract_match_method_no_resolution(self) -> None:
        result = {"order_matched": False}
        method = shadow_eval._extract_match_method(result)
        self.assertEqual(method, "none")

    def test_extract_route_decision_order_status(self) -> None:
        result = {"routing": {"intent": "order_status"}}
        decision = shadow_eval._extract_route_decision(result)
        self.assertEqual(decision, "order_status")

    def test_extract_route_decision_non_order_status(self) -> None:
        result = {"routing": {"intent": "returns"}}
        decision = shadow_eval._extract_route_decision(result)
        self.assertEqual(decision, "non_order_status")

    def test_extract_route_decision_unknown(self) -> None:
        result = {"routing": {}}
        decision = shadow_eval._extract_route_decision(result)
        self.assertEqual(decision, "unknown")

    def test_classify_failure_reason_bucket_no_identifiers(self) -> None:
        result = {"failure_reason": "no_customer_email"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "no_identifiers")

    def test_classify_failure_reason_bucket_shopify_api_error(self) -> None:
        result = {"failure_reason": "shopify_api_error"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "shopify_api_error")

    def test_classify_failure_reason_bucket_richpanel_api_error(self) -> None:
        result = {"failure_reason": "richpanel_error"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "richpanel_api_error")

    def test_classify_failure_reason_bucket_ambiguous_match(self) -> None:
        result = {"failure_reason": "multiple_orders_ambiguous"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "ambiguous_match")

    def test_classify_failure_reason_bucket_no_order_candidates(self) -> None:
        result = {"failure_reason": "no_order_candidates"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "no_order_candidates")

    def test_classify_failure_reason_bucket_parse_error(self) -> None:
        result = {"failure_reason": "parse_error"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "parse_error")

    def test_classify_failure_reason_bucket_none(self) -> None:
        result = {}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertIsNone(bucket)

    def test_classify_failure_reason_bucket_shopify_timeout(self) -> None:
        """Test that shopify_timeout is correctly classified as shopify_api_error."""
        result = {"failure_reason": "shopify_timeout"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "shopify_api_error")

    def test_classify_failure_reason_bucket_shopify_401(self) -> None:
        """Test that shopify_401 is correctly classified as shopify_api_error."""
        result = {"failure_reason": "shopify_401"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "shopify_api_error")

    def test_classify_failure_reason_bucket_shopify_5xx(self) -> None:
        """Test that shopify_5xx is correctly classified as shopify_api_error."""
        result = {"failure_reason": "shopify_5xx"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "shopify_api_error")

    def test_classify_failure_reason_bucket_richpanel_timeout(self) -> None:
        """Test that richpanel_timeout is correctly classified as richpanel_api_error."""
        result = {"failure_reason": "richpanel_timeout"}
        bucket = shadow_eval._classify_failure_reason_bucket(result)
        self.assertEqual(bucket, "richpanel_api_error")

    def test_failure_buckets_are_pii_safe(self) -> None:
        """
        Test that failure buckets do not contain PII even when input has PII.
        This verifies the PII safety claim in the PR.
        """
        # Test with failure reason containing email
        result_with_email = {"failure_reason": "customer email customer@example.com not found"}
        bucket = shadow_eval._classify_failure_reason_bucket(result_with_email)
        self.assertIsNotNone(bucket)
        self.assertNotIn("customer@example.com", bucket)
        self.assertNotIn("@", bucket)
        
        # Test with failure reason containing order number
        result_with_order = {"failure_reason": "order #12345 not found"}
        bucket = shadow_eval._classify_failure_reason_bucket(result_with_order)
        self.assertIsNotNone(bucket)
        self.assertNotIn("12345", bucket)
        self.assertNotIn("#", bucket)
        
        # Test with failure reason containing customer name
        result_with_name = {"failure_reason": "customer John Doe not found"}
        bucket = shadow_eval._classify_failure_reason_bucket(result_with_name)
        self.assertIsNotNone(bucket)
        self.assertNotIn("John", bucket)
        self.assertNotIn("Doe", bucket)
        
        # Verify all buckets are from the expected PII-safe set
        expected_buckets = {
            "no_identifiers",
            "shopify_api_error",
            "richpanel_api_error",
            "ambiguous_match",
            "no_order_candidates",
            "parse_error",
            "other_error",
            "other_failure",
        }
        for test_result in [result_with_email, result_with_order, result_with_name]:
            bucket = shadow_eval._classify_failure_reason_bucket(test_result)
            self.assertIn(bucket, expected_buckets, 
                         f"Bucket '{bucket}' not in expected PII-safe set")

    def test_route_decision_is_pii_safe(self) -> None:
        """Test that route decisions do not contain PII."""
        # Test with routing containing customer info
        result = {
            "routing": {
                "intent": "order_status",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe"
            }
        }
        decision = shadow_eval._extract_route_decision(result)
        self.assertIsNotNone(decision)
        self.assertNotIn("customer@example.com", decision)
        self.assertNotIn("@", decision)
        self.assertNotIn("John", decision)
        self.assertNotIn("Doe", decision)
        # Decision should only be one of the expected values
        self.assertIn(decision, {"order_status", "non_order_status", "unknown"})

    def test_match_method_is_pii_safe(self) -> None:
        """Test that match methods do not contain PII."""
        # Test with order resolution containing PII
        result = {
            "order_matched": True,
            "order_resolution": {
                "resolvedBy": "shopify_email_name",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "order_number": "12345"
            }
        }
        method = shadow_eval._extract_match_method(result)
        self.assertIsNotNone(method)
        self.assertNotIn("customer@example.com", method)
        self.assertNotIn("@", method)
        self.assertNotIn("John", method)
        self.assertNotIn("Doe", method)
        self.assertNotIn("12345", method)
        # Method should only be one of the expected values
        self.assertIn(method, {"order_number", "name_email", "email_only", "none", "parse_error"})

    def test_build_drift_watch_no_alerts(self) -> None:
        drift_watch = shadow_eval._build_drift_watch(
            match_rate=0.95,
            api_error_rate=0.02,
            order_number_share=0.60,
            schema_new_ratio=0.10,
        )
        self.assertFalse(drift_watch["has_alerts"])
        self.assertEqual(len(drift_watch["alerts"]), 0)
        self.assertEqual(drift_watch["current_values"]["match_rate_pct"], 95.0)
        self.assertEqual(drift_watch["current_values"]["api_error_rate_pct"], 2.0)

    def test_build_drift_watch_api_error_alert(self) -> None:
        drift_watch = shadow_eval._build_drift_watch(
            match_rate=0.95,
            api_error_rate=0.08,  # Above 5% threshold
            order_number_share=0.60,
            schema_new_ratio=0.10,
        )
        self.assertTrue(drift_watch["has_alerts"])
        self.assertEqual(len(drift_watch["alerts"]), 1)
        self.assertEqual(drift_watch["alerts"][0]["metric"], "api_error_rate")

    def test_build_drift_watch_schema_drift_alert(self) -> None:
        drift_watch = shadow_eval._build_drift_watch(
            match_rate=0.95,
            api_error_rate=0.02,
            order_number_share=0.60,
            schema_new_ratio=0.25,  # Above 20% threshold
        )
        self.assertTrue(drift_watch["has_alerts"])
        self.assertEqual(len(drift_watch["alerts"]), 1)
        self.assertEqual(drift_watch["alerts"][0]["metric"], "schema_drift")

    def test_build_drift_watch_multiple_alerts(self) -> None:
        drift_watch = shadow_eval._build_drift_watch(
            match_rate=0.95,
            api_error_rate=0.10,  # Above 5% threshold
            order_number_share=0.60,
            schema_new_ratio=0.30,  # Above 20% threshold
        )
        self.assertTrue(drift_watch["has_alerts"])
        self.assertEqual(len(drift_watch["alerts"]), 2)

    def test_drift_watch_ignores_noisy_schema_keys(self) -> None:
        payloads = []
        for idx in range(6):
            payloads.append(
                {
                    "id": f"t-{idx}",
                    "created_at": f"2025-01-{idx + 1:02d}T00:00:00Z",
                    "updated_at": f"2025-01-{idx + 1:02d}T01:00:00Z",
                    "status": "open",
                    "customer": {
                        "email": f"user{idx}@example.com",
                        "name": "Test User",
                    },
                    "custom_fields": {"Order Number": str(1000 + idx)},
                    "comments": [
                        {
                            "body": f"Message {idx}",
                            "created_at": f"2025-01-{idx + 1:02d}T00:00:00Z",
                        }
                    ],
                    "tags": ["tag", str(idx)],
                    "metadata": {"page": idx, "cursor": f"c{idx}"},
                }
            )
        fingerprints = [
            fp for fp in (shadow_eval._schema_fingerprint(p) for p in payloads) if fp
        ]
        schema_new_ratio = len(set(fingerprints)) / len(fingerprints)
        drift_watch = shadow_eval._build_drift_watch(
            match_rate=1.0,
            api_error_rate=0.0,
            order_number_share=1.0,
            schema_new_ratio=schema_new_ratio,
        )
        self.assertFalse(drift_watch["has_alerts"])
        self.assertEqual(len(drift_watch["alerts"]), 0)

    def test_drift_watch_catches_real_schema_drift(self) -> None:
        payloads = [
            {"status": "open", "customer": {"email": "a@example.com"}},
            {"status": "open", "customer": {"email": "b@example.com"}},
            {"status": "open", "customer": {"email": "c@example.com"}},
            {"status": "open", "customer": {"email": "d@example.com"}},
            {"state": "open", "customer": {"email": "e@example.com"}},
        ]
        fingerprints = [
            fp for fp in (shadow_eval._schema_fingerprint(p) for p in payloads) if fp
        ]
        schema_new_ratio = len(set(fingerprints)) / len(fingerprints)
        drift_watch = shadow_eval._build_drift_watch(
            match_rate=1.0,
            api_error_rate=0.0,
            order_number_share=1.0,
            schema_new_ratio=schema_new_ratio,
        )
        self.assertTrue(drift_watch["has_alerts"])
        self.assertEqual(len(drift_watch["alerts"]), 1)
        self.assertEqual(drift_watch["alerts"][0]["metric"], "schema_drift")

    def test_drift_watch_excludes_ticket_fetch_failed_from_api_errors(self) -> None:
        ticket_results = [
            {"failure_source": "richpanel_fetch", "failure_reason": "ticket_fetch_failed"},
            {"failure_source": "richpanel_fetch", "failure_reason": "richpanel_403"},
            {"failure_source": "shopify_fetch", "failure_reason": "shopify_401"},
            {"order_matched": True},
        ]
        drift_watch = shadow_eval._compute_drift_watch(
            ticket_results=ticket_results,
            ticket_schema_total=1,
            ticket_schema_new=0,
            shopify_schema_total=1,
            shopify_schema_new=0,
        )
        self.assertEqual(drift_watch["current_values"]["api_error_rate_pct"], 50.0)
        self.assertEqual(
            drift_watch["current_values"]["ticket_fetch_failure_rate_pct"], 25.0
        )

    def test_schema_skip_descent_keys_log_nested_paths(self) -> None:
        payload = {
            "comments": [
                {"body": "hello", "metadata": {"sentiment": "neutral"}},
                {"body": "bye", "metadata": {"sentiment": "positive"}},
            ],
            "status": "open",
        }
        key_counts = Counter()
        ignored_counts = Counter()
        shadow_eval._schema_fingerprint(
            payload, key_counter=key_counts, ignored_counter=ignored_counts
        )
        self.assertIn("comments", key_counts)
        self.assertIn("comments[]", key_counts)
        self.assertIn("comments[].body", ignored_counts)
        self.assertIn("comments[].metadata", ignored_counts)


class LiveReadonlyShadowEvalHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._preflight_patch = mock.patch.object(
            shadow_eval,
            "run_secrets_preflight",
            return_value={"overall_status": "PASS"},
        )
        self._preflight_patch.start()

    def tearDown(self) -> None:
        self._preflight_patch.stop()
        super().tearDown()
    def test_require_prod_environment_blocks_non_prod(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            with self.assertRaises(SystemExit):
                shadow_eval._require_prod_environment(allow_non_prod=False)
            self.assertEqual(
                shadow_eval._require_prod_environment(allow_non_prod=True), "dev"
            )

    def test_resolve_env_name_defaults_to_local(self) -> None:
        with mock.patch.dict(os.environ, _with_openai_env({}), clear=True):
            self.assertEqual(shadow_eval._resolve_env_name(), "local")

    def test_sys_path_inserts_backend_src(self) -> None:
        original_path = list(sys.path)
        try:
            src_path = str(shadow_eval.SRC)
            if src_path in sys.path:
                sys.path.remove(src_path)
            importlib.reload(shadow_eval)
            self.assertIn(src_path, sys.path)
        finally:
            sys.path[:] = original_path
            importlib.reload(shadow_eval)

    def test_resolve_env_name_prefers_richpanel_env(self) -> None:
        env = {
            "RICHPANEL_ENV": "Staging",
            "MW_ENV": "prod",
            "SHOPIFY_SHOP_DOMAIN": "test-shop.myshopify.com",
        }
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            self.assertEqual(shadow_eval._resolve_env_name(), "staging")

    def test_resolve_richpanel_base_url_override(self) -> None:
        env = {"RICHPANEL_API_BASE_URL": "https://api.richpanel.com/"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            self.assertEqual(
                shadow_eval._resolve_richpanel_base_url(),
                "https://api.richpanel.com",
            )

    def test_require_env_flags_success(self) -> None:
        env = {
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            applied = shadow_eval._require_env_flags("test")
        self.assertEqual(applied, shadow_eval.REQUIRED_FLAGS)

    def test_require_env_flag_mismatch_raises(self) -> None:
        env = {"RICHPANEL_WRITE_DISABLED": "false"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow_eval._require_env_flag(
                    "RICHPANEL_WRITE_DISABLED", "true", context="test"
                )
        self.assertIn("found", str(ctx.exception))

    def test_build_richpanel_client_sets_base_url(self) -> None:
        client = shadow_eval._build_richpanel_client(
            richpanel_secret=None, base_url="https://example.com"
        )
        self.assertEqual(client.base_url, "https://example.com")

    def test_redact_identifier_empty(self) -> None:
        self.assertIsNone(shadow_eval._redact_identifier(""))
        self.assertIsNone(shadow_eval._redact_identifier("   "))

    def test_to_bool_defaults(self) -> None:
        self.assertTrue(shadow_eval._to_bool("maybe", default=True))
        self.assertFalse(shadow_eval._to_bool("maybe", default=False))
        self.assertTrue(shadow_eval._to_bool("YES", default=False))
        self.assertFalse(shadow_eval._to_bool("no", default=True))

    def test_env_truthy_and_openai_flags(self) -> None:
        self.assertFalse(shadow_eval._env_truthy(None))
        self.assertTrue(shadow_eval._env_truthy("true"))
        self.assertTrue(shadow_eval._env_truthy("  YES "))
        with mock.patch.dict(
            os.environ,
            {
                "MW_OPENAI_SHADOW_ENABLED": "true",
                "MW_OPENAI_ROUTING_ENABLED": "true",
            },
            clear=True,
        ):
            self.assertTrue(shadow_eval._openai_shadow_enabled())
            self.assertTrue(shadow_eval._openai_any_enabled())

    def test_identity_block_hashes_api_key(self) -> None:
        class _StubClient:
            base_url = "https://api.richpanel.com"
            api_key_secret_id = "rp-mw/dev/richpanel/api_key"

            def _load_api_key(self) -> str:
                return "test-key"

        started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        identity = shadow_eval._build_identity_block(
            client=_StubClient(),
            env_name="dev",
            started_at=started_at,
            duration_seconds=1.234,
        )
        expected_hash = hashlib.sha256(b"test-key").hexdigest()[:8]
        self.assertEqual(identity.get("api_key_hash"), expected_hash)
        self.assertIsNone(identity.get("api_key_error"))

    def test_identity_block_handles_api_key_error(self) -> None:
        class _StubClient:
            base_url = "https://api.richpanel.com"
            api_key_secret_id = "rp-mw/dev/richpanel/api_key"

            def _load_api_key(self) -> str:
                raise RuntimeError("boom")

        started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        identity = shadow_eval._build_identity_block(
            client=_StubClient(),
            env_name="dev",
            started_at=started_at,
            duration_seconds=0.1,
        )
        self.assertIsNone(identity.get("api_key_hash"))
        self.assertEqual(identity.get("api_key_error"), "RuntimeError")

    def test_request_burst_and_retry_after_helpers(self) -> None:
        timestamps = [1.0, 2.0, 3.0, 40.0]
        self.assertEqual(shadow_eval._max_requests_in_window(timestamps, 30), 3)
        burst = shadow_eval._summarize_request_burst(
            [
                {"timestamp": 1.0, "path": "/v1/tickets"},
                {"timestamp": 2.0, "path": "/v1/tickets"},
                {"timestamp": 3.0, "path": "/v1/tickets"},
                {"timestamp": 40.0, "path": "/v1/other"},
            ],
            window_seconds=30,
        )
        self.assertEqual(burst.get("max_requests_overall"), 3)
        self.assertEqual(burst.get("max_requests_by_endpoint")[0]["path"], "/v1/tickets")
        retry = shadow_eval._summarize_retry_after(
            [
                {"retry_after": 3, "retry_delay_seconds": 4},
                {"retry_after": 5, "retry_delay_seconds": 4},
            ]
        )
        self.assertEqual(retry.get("checked"), 2)
        self.assertEqual(retry.get("violations"), 1)

    def test_markdown_report_includes_trace_sections(self) -> None:
        report = {
            "http_trace_summary": {},
            "richpanel_request_burst": {"max_requests_overall": 5},
            "richpanel_retry_after_validation": {"checked": 2, "violations": 0},
            "richpanel_identity": {
                "richpanel_base_url": "https://api.richpanel.com",
                "resolved_env": "dev",
                "api_key_hash": "abc12345",
                "api_key_secret_id": "rp-mw/dev/richpanel/api_key",
            },
        }
        markdown_lines = shadow_eval._build_markdown_report(report, summary_payload={})
        markdown = "\n".join(markdown_lines)
        self.assertIn("Richpanel Burst Summary", markdown)
        self.assertIn("Retry-After Validation", markdown)
        self.assertIn("Richpanel Identity", markdown)

    def test_redact_identifier_none(self) -> None:
        self.assertIsNone(shadow_eval._redact_identifier(None))

    def test_normalize_optional_text_handles_exception(self) -> None:
        class _BadStr:
            def __str__(self) -> str:
                raise ValueError("boom")

        self.assertEqual(shadow_eval._normalize_optional_text(_BadStr()), "")

    def test_channel_extraction_and_classification(self) -> None:
        self.assertEqual(shadow_eval._extract_channel(["not", "dict"]), "")
        self.assertEqual(
            shadow_eval._extract_channel({"via": {"channel": "Email"}}), "email"
        )
        self.assertEqual(
            shadow_eval._extract_channel({"channel": "chat"}), "chat"
        )
        self.assertEqual(shadow_eval._classify_channel("email"), "email")
        self.assertEqual(shadow_eval._classify_channel("webchat"), "chat")
        self.assertEqual(shadow_eval._classify_channel("phone"), "unknown")
        self.assertEqual(shadow_eval._classify_channel(""), "unknown")

    def test_schema_helpers_cover_edges(self) -> None:
        keys: set[str] = set()
        shadow_eval._collect_schema_key_paths(
            {"a": {"b": {"c": 1}}}, keys=keys, max_depth=0
        )
        self.assertTrue(keys)
        keys = set()
        shadow_eval._collect_schema_key_paths(
            {"a": {"b": {"c": 1}}}, keys=keys, depth=2, max_depth=1
        )
        self.assertFalse(keys)
        keys = set()
        shadow_eval._collect_schema_key_paths([{"id": 1}], keys=keys)
        self.assertIn("[]", keys)

        self.assertIsNone(shadow_eval._schema_fingerprint("not-iterable"))
        self.assertEqual(shadow_eval._percentile([], 50), 0.0)

    def test_classify_helpers(self) -> None:
        self.assertTrue(shadow_eval._is_timeout_error(RuntimeError("timeout")))
        self.assertEqual(shadow_eval._classify_status_code("shopify", 401), "shopify_401")
        self.assertEqual(shadow_eval._classify_status_code("shopify", 403), "shopify_403")
        self.assertEqual(shadow_eval._classify_status_code("shopify", 404), "shopify_404")
        self.assertEqual(shadow_eval._classify_status_code("shopify", 429), "shopify_429")
        self.assertEqual(shadow_eval._classify_status_code("shopify", 500), "shopify_5xx")
        self.assertEqual(shadow_eval._classify_status_code("shopify", 418), "shopify_4xx")
        self.assertEqual(shadow_eval._classify_status_code("shopify", 200), "shopify_status")
        self.assertEqual(shadow_eval._classify_status_code("shopify", None), "shopify_error")

        richpanel_exc = shadow_eval.RichpanelRequestError(
            "boom", response=SimpleNamespace(status_code=401)
        )
        self.assertEqual(
            shadow_eval._classify_richpanel_exception(richpanel_exc), "richpanel_401"
        )
        self.assertEqual(
            shadow_eval._classify_richpanel_exception(
                shadow_eval.TransportError("timeout")
            ),
            "richpanel_timeout",
        )
        self.assertEqual(
            shadow_eval._classify_richpanel_exception(shadow_eval.TransportError("boom")),
            "richpanel_transport_error",
        )
        self.assertEqual(
            shadow_eval._classify_richpanel_exception(shadow_eval.SecretLoadError("boom")),
            "richpanel_secret_load_error",
        )
        self.assertEqual(
            shadow_eval._classify_richpanel_exception(RuntimeError("timeout")),
            "richpanel_timeout",
        )
        self.assertEqual(
            shadow_eval._classify_richpanel_exception(RuntimeError("boom")),
            "richpanel_error",
        )

        shopify_exc = shadow_eval.ShopifyRequestError(
            "boom", response=SimpleNamespace(status_code=401)
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(shopify_exc), "shopify_401"
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(
                shadow_eval.ShopifyTransportError("timeout")
            ),
            "shopify_timeout",
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(
                shadow_eval.ShopifyTransportError("boom")
            ),
            "shopify_transport_error",
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(shadow_eval.ShopifyRequestError("timeout")),
            "shopify_timeout",
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(shadow_eval.ShopifyRequestError("boom")),
            "shopify_error",
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(RuntimeError("timeout")),
            "shopify_timeout",
        )
        self.assertEqual(
            shadow_eval._classify_shopify_exception(RuntimeError("boom")),
            "shopify_error",
        )

        self.assertEqual(
            shadow_eval._map_order_resolution_reason("no_email_available"),
            "no_customer_email",
        )
        self.assertEqual(
            shadow_eval._classify_order_match_failure(
                {
                    "order_matched": False,
                    "order_resolution": {"reason": "no_email_available"},
                }
            ),
            "no_customer_email",
        )
        self.assertEqual(
            shadow_eval._classify_order_match_failure(
                {
                    "order_matched": False,
                    "order_resolution": {"resolvedBy": "no_match"},
                }
            ),
            "no_order_candidates",
        )
        self.assertEqual(
            shadow_eval._classify_order_match_failure(
                {
                    "order_matched": False,
                    "order_resolution": {
                        "resolvedBy": "no_match",
                        "shopify_diagnostics": {"category": "auth_fail"},
                    },
                }
            ),
            "shopify_auth_fail",
        )
        self.assertEqual(
            shadow_eval._classify_order_match_failure(
                {"order_matched": False, "order_status_candidate": False}
            ),
            "no_order_status_candidate",
        )
        self.assertEqual(
            shadow_eval._classify_order_match_failure({"order_matched": False}),
            "order_match_failed",
        )
        self.assertIsNone(
            shadow_eval._classify_order_match_failure({"order_matched": True})
        )

    def test_classify_match_failure_bucket(self) -> None:
        self.assertIsNone(
            shadow_eval._classify_match_failure_bucket({"order_matched": True})
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket({"order_matched": False}),
            "unknown",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {"order_matched": False, "failure_reason": "no_customer_email"}
            ),
            "no_email",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {
                    "order_matched": False,
                    "failure_reason": "multiple_orders_ambiguous",
                }
            ),
            "ambiguous_customer",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {
                    "order_matched": False,
                    "failure_reason": "no_order_candidates",
                    "order_number_present": False,
                }
            ),
            "no_order_number",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {
                    "order_matched": False,
                    "failure_reason": "no_order_candidates",
                    "order_number_present": True,
                }
            ),
            "no_order_candidates",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {
                    "order_matched": False,
                    "failure_reason": "no_order_status_candidate",
                    "order_number_present": True,
                }
            ),
            "order_match_failed",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {"order_matched": False, "failure_reason": "parse_error"}
            ),
            "parse_error",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {"order_matched": False, "failure_reason": "shopify_401"}
            ),
            "api_error",
        )
        self.assertEqual(
            shadow_eval._classify_match_failure_bucket(
                {"order_matched": False, "failure_reason": "something_else"}
            ),
            "other_failure",
        )

    def test_schema_fingerprint_deterministic(self) -> None:
        payload_a = {
            "id": "t-1",
            "customer": {"email": "a@example.com", "name": "A"},
            "orders": [{"id": "o-1"}],
            "__source_path": "/v1/tickets/1",
        }
        payload_b = {
            "orders": [{"id": "o-2"}],
            "customer": {"email": "b@example.com", "name": "B"},
            "id": "t-2",
        }
        payload_c = {
            "orders": [{"id": "o-3"}],
            "customer": {"name": "C"},
            "id": "t-3",
            "new_field": {"sub": 1},
        }
        fingerprint_a = shadow_eval._schema_fingerprint(payload_a)
        fingerprint_b = shadow_eval._schema_fingerprint(payload_b)
        fingerprint_c = shadow_eval._schema_fingerprint(payload_c)
        self.assertEqual(fingerprint_a, fingerprint_b)
        self.assertNotEqual(fingerprint_a, fingerprint_c)

    def test_build_summary_payload_rollups(self) -> None:
        ticket_results = [
            {
                "channel": "email",
                "order_matched": True,
                "tracking_found": True,
                "eta_available": True,
                "would_reply_send": True,
            },
            {
                "channel": "chat",
                "order_matched": False,
                "failure_reason": "no_customer_email",
                "failure_source": "order_match",
                "order_number_present": False,
            },
            {
                "channel": "unknown",
                "order_matched": False,
                "failure_reason": "no_order_candidates",
                "failure_source": "order_match",
                "order_number_present": True,
            },
            {
                "channel": "email",
                "order_matched": False,
                "failure_reason": "shopify_401",
                "failure_source": "shopify_fetch",
            },
            {
                "channel": "email",
                "order_matched": False,
                "failure_reason": "richpanel_timeout",
                "failure_source": "richpanel_fetch",
            },
        ]
        timing = shadow_eval._summarize_timing(
            [0.1, 0.2, 0.3], run_duration_seconds=0.6
        )
        drift = shadow_eval._build_drift_summary(
            ticket_total=4,
            ticket_new=1,
            ticket_unique=1,
            shopify_total=2,
            shopify_new=1,
            shopify_unique=1,
            threshold=0.2,
        )
        summary = shadow_eval._build_summary_payload(
            run_id="RUN_TEST",
            tickets_requested=5,
            ticket_results=ticket_results,
            timing=timing,
            drift=drift,
        )
        self.assertEqual(summary["ticket_count"], 5)
        self.assertEqual(summary["tickets_evaluated"], 5)
        self.assertEqual(summary["email_channel_count"], 3)
        self.assertEqual(summary["chat_channel_count"], 1)
        self.assertEqual(summary["unknown_channel_count"], 1)
        self.assertEqual(summary["order_match_success_count"], 1)
        self.assertEqual(summary["order_match_failure_count"], 4)
        self.assertEqual(summary["match_success_rate"], 0.2)
        self.assertEqual(summary["tracking_or_eta_available_count"], 1)
        self.assertEqual(summary["tracking_or_eta_available_rate"], 0.2)
        self.assertTrue(summary["would_reply_send"])
        self.assertEqual(summary["failure_reasons"]["shopify_401"], 1)
        self.assertEqual(summary["failure_reasons"]["richpanel_timeout"], 1)
        self.assertEqual(summary["shopify_fetch_failures"]["shopify_401"], 1)
        self.assertEqual(summary["richpanel_fetch_failures"]["richpanel_timeout"], 1)
        self.assertEqual(summary["match_failure_buckets"]["no_email"], 1)
        self.assertEqual(summary["match_failure_buckets"]["no_order_candidates"], 1)
        self.assertEqual(summary["match_failure_buckets"]["api_error"], 2)

    def test_build_shopify_client(self) -> None:
        client = shadow_eval._build_shopify_client(
            allow_network=False, shop_domain="example.myshopify.com"
        )
        self.assertEqual(client.shop_domain, "example.myshopify.com")

    def test_is_prod_target_detects_env(self) -> None:
        env = {"MW_ENV": "prod", "SHOPIFY_SHOP_DOMAIN": "test-shop.myshopify.com"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url=shadow_eval.PROD_RICHPANEL_BASE_URL,
                richpanel_secret_id=None,
            )
        self.assertTrue(result)

    def test_is_prod_target_detects_prod_key_and_base(self) -> None:
        env = {"PROD_RICHPANEL_API_KEY": "token-value"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url=shadow_eval.PROD_RICHPANEL_BASE_URL,
                richpanel_secret_id=None,
            )
        self.assertTrue(result)

    def test_is_prod_target_detects_secret_hint(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url="https://sandbox.richpanel.com",
                richpanel_secret_id="arn:aws:secretsmanager:us-east-2:123:secret/prod/rp",
            )
        self.assertTrue(result)

    def test_is_prod_target_false_for_non_prod(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url="https://sandbox.richpanel.com",
                richpanel_secret_id=None,
            )
        self.assertFalse(result)

    def test_redact_path_hashes_ids(self) -> None:
        redacted = shadow_eval._redact_path("/v1/tickets/91608")
        self.assertTrue(redacted.startswith("/v1/tickets/"))
        self.assertIn("redacted:", redacted)
        self.assertNotIn("91608", redacted)

    def test_redact_path_handles_empty(self) -> None:
        self.assertEqual(shadow_eval._redact_path(""), "/")

    def test_redact_path_keeps_alpha_segment(self) -> None:
        redacted = shadow_eval._redact_path("/api/v1/orders/ABC")
        self.assertIn("/ABC", redacted)
        self.assertNotIn("redacted:", redacted)

    def test_extract_latest_customer_message(self) -> None:
        ticket = {"customer_note": "ticket message"}
        convo = {"messages": [{"sender_type": "customer", "body": "later message"}]}
        message = shadow_eval._extract_latest_customer_message(ticket, convo)
        self.assertEqual(message, "ticket message")

        ticket = {
            "comments": [
                {"plain_body": "customer comment", "via": {"isOperator": False}}
            ]
        }
        message = shadow_eval._extract_latest_customer_message(ticket, {})
        self.assertEqual(message, "customer comment")

        ticket = {
            "comments": [
                {"plain_body": "agent note", "via": {"isOperator": True}},
                {"body": "customer followup", "via": {"isOperator": False}},
            ]
        }
        message = shadow_eval._extract_latest_customer_message(ticket, {})
        self.assertEqual(message, "customer followup")

        message = shadow_eval._extract_latest_customer_message(
            {},
            {
                "messages": [
                    {"sender_type": "operator", "body": "ignore"},
                    {"sender_type": "customer", "body": "from convo"},
                ]
            },
        )
        self.assertEqual(message, "from convo")

        ticket = {}
        convo = {"body": "conversation message"}
        message = shadow_eval._extract_latest_customer_message(ticket, convo)
        self.assertEqual(message, "conversation message")

        convo = {
            "messages": [
                {"sender_type": "agent", "body": "ignore"},
                {"sender_type": "customer", "body": "need tracking"},
            ]
        }
        message = shadow_eval._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "need tracking")

        convo = {
            "comments": [
                {"body": "from convo comment", "via": {"isOperator": False}}
            ]
        }
        message = shadow_eval._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "from convo comment")

        convo = {
            "messages": [
                {"sender_type": " customer ", "body": "trimmed sender"},
            ]
        }
        message = shadow_eval._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "trimmed sender")

        convo = {
            "messages": [
                {"body": "system message"},
                {"sender_type": "customer", "body": "real customer"},
            ]
        }
        message = shadow_eval._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "real customer")

        convo = {"messages": ["not-a-dict", {"sender_type": "agent", "body": "ignore"}]}
        message = shadow_eval._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "")

    def test_require_env_flag_missing_raises(self) -> None:
        with mock.patch.dict(os.environ, _with_openai_env({}), clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow_eval._require_env_flag(
                    "RICHPANEL_WRITE_DISABLED", "true", context="test"
                )
        self.assertIn("unset", str(ctx.exception))

    def test_fetch_recent_ticket_refs_success(self) -> None:
        payload = {
            "tickets": [
                {"id": "t-1"},
                {"conversation_no": "1001"},
                {"id": "t-1"},
            ]
        }
        client = _ListingClient(payload)
        results = shadow_eval._fetch_recent_ticket_refs(
            client, sample_size=2, list_path="/v1/tickets"
        )
        self.assertEqual(results, ["t-1", "1001"])

    def test_fetch_recent_ticket_refs_errors_on_status(self) -> None:
        client = _ListingClient({}, status_code=500)
        with self.assertRaises(SystemExit):
            shadow_eval._fetch_recent_ticket_refs(
                client, sample_size=1, list_path="/v1/tickets"
            )

    def test_fetch_recent_ticket_refs_fallbacks_on_forbidden(self) -> None:
        payload = {
            "data": [
                {"id": "c-1"},
                {"conversation_no": "1002"},
            ]
        }
        client = _FallbackListingClient(payload)
        results = shadow_eval._fetch_recent_ticket_refs(
            client, sample_size=2, list_path="/v1/tickets"
        )
        self.assertEqual(results, ["c-1", "1002"])
        self.assertEqual(
            client.paths,
            ["/v1/tickets", "/api/v1/conversations", "/v1/conversations"],
        )

    def test_comment_is_operator_detection(self) -> None:
        self.assertTrue(shadow_eval._comment_is_operator({"is_operator": True}))
        self.assertFalse(shadow_eval._comment_is_operator({"isOperator": False}))
        self.assertTrue(
            shadow_eval._comment_is_operator({"via": {"isOperator": True}})
        )
        self.assertTrue(
            shadow_eval._comment_is_operator({"via": {"is_operator": True}})
        )
        self.assertIsNone(shadow_eval._comment_is_operator({"via": "not-a-dict"}))
        self.assertIsNone(shadow_eval._comment_is_operator({}))

    def test_extract_comment_message_variants(self) -> None:
        payload = {"comments": "not-a-list"}
        self.assertEqual(shadow_eval._extract_comment_message(payload), "")

        payload = {
            "comments": [
                "not-a-dict",
                {"plain_body": "agent note", "via": {"isOperator": True}},
                {"body": "customer body", "via": {"isOperator": False}},
            ]
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "customer body")

        payload = {
            "comments": [
                {"plain_body": "  ", "via": {"isOperator": False}},
                {"body": "customer plain", "via": {"isOperator": False}},
            ]
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "customer plain")

        payload = {
            "comments": [
                {"message": "customer message", "via": {"isOperator": False}},
            ]
        }
        self.assertEqual(
            shadow_eval._extract_comment_message(
                payload, extractor=shadow_eval.extract_customer_message
            ),
            "customer message",
        )

        payload = {
            "ticket": {
                "comments": [
                    {
                        "plain_body": "agent email",
                        "via": {"isOperator": True, "channel": "email"},
                        "created_at": "2026-01-24T06:00:00Z",
                    },
                    {
                        "plain_body": "customer chat",
                        "via": {"isOperator": False, "channel": "chat"},
                        "created_at": "2026-01-24T05:00:00Z",
                    },
                ]
            }
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "customer chat")

        payload = {
            "comments": [
                {
                    "plain_body": "newer chat",
                    "via": {"channel": "chat"},
                    "created_at": "2026-01-24T06:10:00Z",
                },
                {
                    "plain_body": "older email",
                    "via": {"channel": "email"},
                    "created_at": "2026-01-24T06:00:00Z",
                },
            ]
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "older email")

        payload = {
            "comments": [
                {
                    "plain_body": "older email",
                    "via": {"channel": "email"},
                    "created_at": "2026-01-24T06:00:00Z",
                },
                {
                    "plain_body": "newer email",
                    "via": {"channel": "email"},
                    "created_at": "2026-01-24T06:10:00Z",
                },
            ]
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "newer email")

        payload = {
            "comments": [
                {
                    "plain_body": "longer message here",
                    "via": {"channel": "email"},
                },
                {
                    "plain_body": "short",
                    "via": {"channel": "email"},
                },
            ]
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "short")

        payload = {
            "comments": [
                {"body": "operator note", "via": {"isOperator": True}},
                {"body": "unknown note", "via": {}},
            ]
        }
        self.assertEqual(shadow_eval._extract_comment_message(payload), "unknown note")

        def _simple_extractor(comment):
            return comment.get("text", "")

        payload = {"comments": [{"text": "fallback text", "via": {"channel": "email"}}]}
        self.assertEqual(
            shadow_utils.extract_comment_message(payload, extractor=_simple_extractor),
            "fallback text",
        )

    def test_parse_timestamp_variants(self) -> None:
        self.assertIsNone(shadow_utils._parse_timestamp(None))
        self.assertIsNone(shadow_utils._parse_timestamp("not-a-time"))
        self.assertIsNotNone(
            shadow_utils._parse_timestamp("2026-01-24T06:10:00Z")
        )
        self.assertIsNotNone(
            shadow_utils._parse_timestamp("2026-01-24T06:10:00+00:00")
        )
        self.assertIsNotNone(
            shadow_utils._parse_timestamp("2026-01-24T06:10:00")
        )

    def test_summarize_comment_metadata(self) -> None:
        payload = {"comments": "not-a-list"}
        meta = shadow_utils.summarize_comment_metadata(payload)
        self.assertEqual(meta["comment_count"], 0)
        self.assertFalse(meta["comment_text_present"])
        self.assertFalse(meta["comment_operator_flag_present"])
        self.assertFalse(meta["customer_comment_present"])

        payload = {
            "ticket": {
                "comments": [
                    {"plain_body": "agent", "via": {"isOperator": True}},
                    {"body": "customer", "via": {"isOperator": False}},
                    {"body": "  ", "via": {"isOperator": False}},
                ]
            }
        }
        meta = shadow_utils.summarize_comment_metadata(payload)
        self.assertEqual(meta["comment_count"], 3)
        self.assertTrue(meta["comment_text_present"])
        self.assertTrue(meta["comment_operator_flag_present"])
        self.assertTrue(meta["customer_comment_present"])

    def test_extract_order_number(self) -> None:
        payload = {"subject": "Order #1057300 missing"}
        self.assertEqual(shadow_utils.extract_order_number(payload), "1057300")
        payload = {"comments": [{"body": "order number: 1185086"}]}
        self.assertEqual(shadow_utils.extract_order_number(payload), "1185086")
        payload = {"ticket": {"comments": [{"plain_body": "orderNumber: 1121654"}]}}
        self.assertEqual(shadow_utils.extract_order_number(payload), "1121654")
        payload = {
            "comments": [
                {"plain_body": "#1234"},
                {"plain_body": "orderNumber: 99999"},
            ]
        }
        self.assertEqual(shadow_utils.extract_order_number(payload), "99999")
        payload = {"custom_fields": {"order_number": "1234567"}}
        self.assertEqual(shadow_utils.extract_order_number(payload), "1234567")
        payload = {"order": {"name": "#2223334"}}
        self.assertEqual(shadow_utils.extract_order_number(payload), "2223334")
        payload = {"messages": [{"text": "Order no. 7654321"}]}
        self.assertEqual(shadow_utils.extract_order_number(payload), "7654321")
        payload = {"order_number": "#1,234,567"}
        self.assertEqual(shadow_utils.extract_order_number(payload), "1234567")
        payload = {"custom_fields": {"shipping_code": "9999999"}}
        self.assertEqual(shadow_utils.extract_order_number(payload), "")

    def test_shadow_utils_list_and_fetch_edge_cases(self) -> None:
        self.assertEqual(
            shadow_utils.extract_ticket_list([{"id": "t-1"}, "bad"]),
            [{"id": "t-1"}],
        )
        self.assertEqual(shadow_utils.extract_ticket_list({"foo": "bar"}), [])
        self.assertEqual(shadow_utils.extract_ticket_list({"data": []}), [])
        with self.assertRaises(SystemExit):
            shadow_utils.fetch_recent_ticket_refs(
                _ListingClient({}), sample_size=0, list_path="/v1/tickets"
            )

        class _DryRunClient(_ListingClient):
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                return _StubResponse({}, status_code=200, dry_run=True)

        with self.assertRaises(SystemExit):
            shadow_utils.fetch_recent_ticket_refs(
                _DryRunClient({}), sample_size=1, list_path="/v1/tickets"
            )

        class _SkipClient(_ListingClient):
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                payload = {"tickets": [{"id": ""}, {"id": "t-1"}, {"id": "t-1"}]}
                return _StubResponse(payload, status_code=200)

        results = shadow_utils.fetch_recent_ticket_refs(
            _SkipClient({}), sample_size=1, list_path="/v1/tickets"
        )
        self.assertEqual(results, ["t-1"])

    def test_shadow_utils_text_parsing_edges(self) -> None:
        class _BadStr:
            def __str__(self) -> str:
                raise ValueError("boom")

        payload = {"comments": [{"plain_body": _BadStr()}]}
        meta = shadow_utils.summarize_comment_metadata(payload)
        self.assertFalse(meta["comment_text_present"])

        self.assertEqual(shadow_utils._coerce_order_number("   "), "")
        self.assertEqual(shadow_utils._coerce_order_number(_BadStr()), "")
        self.assertEqual(shadow_utils._extract_order_number_from_text(""), "")
        self.assertEqual(
            shadow_utils._extract_order_number_from_text("no order here"), ""
        )

        self.assertEqual(shadow_utils._iter_comment_texts({"comments": "nope"}), [])
        self.assertEqual(
            shadow_utils._iter_comment_texts({"comments": ["bad", {"plain_body": _BadStr()}]}),
            [],
        )

        payload = {"order": {"number": "1234"}}
        self.assertEqual(shadow_utils.extract_order_number(payload), "1234")

        payload = {"custom_fields": {"order_ref": "orderNumber: 555"}}
        self.assertEqual(shadow_utils.extract_order_number(payload), "555")

        payload = {"messages": ["bad", {"text": "order #888"}]}
        self.assertEqual(shadow_utils.extract_order_number(payload), "888")

        self.assertIsNone(shadow_utils._parse_timestamp(_BadStr()))
        self.assertIsNone(shadow_utils._parse_timestamp(" "))

        message = shadow_utils.extract_comment_message(
            {"comments": [{"plain_body": _BadStr(), "body": "hi"}]}
        )
        self.assertEqual(message, "hi")

    def test_probe_shopify_ok(self) -> None:
        stub_client = SimpleNamespace(
            request=lambda *args, **kwargs: SimpleNamespace(
                status_code=200, dry_run=False
            )
        )
        with mock.patch.object(
            shadow_eval, "_build_shopify_client", return_value=stub_client
        ):
            result = shadow_eval._probe_shopify(shop_domain="example.myshopify.com")
        self.assertTrue(result["ok"])
        self.assertEqual(result["status_code"], 200)
        self.assertFalse(result["dry_run"])

    def test_probe_shopify_dry_run(self) -> None:
        stub_client = SimpleNamespace(
            request=lambda *args, **kwargs: SimpleNamespace(
                status_code=0, dry_run=True
            )
        )
        with mock.patch.object(
            shadow_eval, "_build_shopify_client", return_value=stub_client
        ):
            result = shadow_eval._probe_shopify(shop_domain="example.myshopify.com")
        self.assertFalse(result["ok"])

    def test_http_trace_records_and_asserts(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://api.richpanel.com/v1/tickets/123")
        trace.record("HEAD", "https://api.richpanel.com/v1/tickets/123")
        trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))
        self.assertEqual(trace.entries[0]["method"], "GET")

        trace.record("POST", "https://api.richpanel.com/v1/tickets/123")
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

        trace = shadow_eval._HttpTrace()
        trace.record("POST", "https://api.openai.com/v1/chat/completions")
        trace.assert_read_only(allow_openai=True, trace_path=Path("trace.json"))
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

    def test_http_trace_allows_aws_readonly_ops(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {
                "method": "POST",
                "path": "/",
                "service": "aws_secretsmanager",
                "operation": "GetSecretValue",
            }
        )
        trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

        trace.entries.append(
            {
                "method": "POST",
                "path": "/",
                "service": "aws_secretsmanager",
                "operation": "DeleteSecret",
            }
        )
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

    def test_http_trace_blocks_aws_non_post(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {
                "method": "GET",
                "path": "/",
                "service": "aws_secretsmanager",
                "operation": "GetSecretValue",
            }
        )
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

    def test_http_trace_allows_aws_portal_get(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {"method": "GET", "path": "/federation/credentials", "service": "aws_portal"}
        )
        trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

        trace.entries.append(
            {"method": "PUT", "path": "/federation/credentials", "service": "aws_portal"}
        )
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

    def test_http_trace_service_mapping(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://shop.myshopify.com/admin/api/2024-01/orders/1")
        trace.record("GET", "https://ssapi.shipstation.com/shipments")
        self.assertEqual(trace.entries[0]["service"], "shopify")
        self.assertEqual(trace.entries[1]["service"], "shipstation")

    def test_service_from_hostname(self) -> None:
        self.assertEqual(
            shadow_eval._service_from_hostname("api.richpanel.com"), "richpanel"
        )
        self.assertEqual(
            shadow_eval._service_from_hostname("shop.myshopify.com"), "shopify"
        )
        self.assertEqual(
            shadow_eval._service_from_hostname("ssapi.shipstation.com"), "shipstation"
        )
        self.assertEqual(
            shadow_eval._service_from_hostname("api.openai.com"), "openai"
        )
        self.assertEqual(
            shadow_eval._service_from_hostname("api.anthropic.com"), "anthropic"
        )
        self.assertEqual(
            shadow_eval._service_from_hostname("secretsmanager.us-east-2.amazonaws.com"),
            "aws_secretsmanager",
        )
        self.assertEqual(
            shadow_eval._service_from_hostname("portal.sso.amazonaws.com"),
            "aws_portal",
        )
        self.assertEqual(shadow_eval._service_from_hostname(""), "unknown")

    def test_http_trace_records_anthropic_and_unknown(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("POST", "https://api.anthropic.com/v1/messages")
        trace.record("GET", "https://example.com/unknown")
        self.assertEqual(trace.entries[0]["service"], "anthropic")
        self.assertEqual(trace.entries[1]["service"], "unknown")

    def test_http_trace_capture_handles_bad_request(self) -> None:
        class _BadRequest:
            def get_method(self):
                raise ValueError("boom")

        trace = shadow_eval._HttpTrace()
        original_urlopen = shadow_eval.urllib.request.urlopen
        shadow_eval.urllib.request.urlopen = lambda *args, **kwargs: SimpleNamespace()
        try:
            trace.capture()
            shadow_eval.urllib.request.urlopen(_BadRequest())
        finally:
            trace.stop()
            shadow_eval.urllib.request.urlopen = original_urlopen

    def test_http_trace_assert_read_only_unknown_service(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append({"method": "GET", "path": "/x", "service": "unknown"})
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

    def test_http_trace_capture_wraps_urlopen(self) -> None:
        trace = shadow_eval._HttpTrace()
        calls = []

        def fake_urlopen(req, *args, **kwargs):
            calls.append(req)

            class _DummyResponse:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def read(self):
                    return b""

                @property
                def headers(self):
                    return {}

                def getcode(self):
                    return 200

            return _DummyResponse()

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            trace.capture()
            request = shadow_eval.urllib.request.Request(
                "https://api.richpanel.com/v1/tickets/123", method="GET"
            )
            shadow_eval.urllib.request.urlopen(request)
            trace.stop()

        self.assertTrue(calls)
        self.assertTrue(trace.entries)
        self.assertEqual(trace.entries[0]["service"], "richpanel")

    def test_http_trace_to_dict(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://api.richpanel.com/v1/tickets/123")
        payload = trace.to_dict()
        self.assertIn("generated_at", payload)
        self.assertEqual(len(payload["entries"]), 1)
        trace._aws_trace.error = "botocore_unavailable"
        payload = trace.to_dict()
        self.assertEqual(payload.get("aws_sdk_trace_error"), "botocore_unavailable")

    def test_summarize_trace_counts(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://api.richpanel.com/v1/tickets/123")
        trace.record("HEAD", "https://api.richpanel.com/v1/tickets/123")
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertEqual(summary["total_requests"], 2)
        self.assertTrue(summary["allowed_methods_only"])
        self.assertEqual(summary["methods"].get("GET"), 1)

    def test_summarize_trace_allows_openai_when_enabled(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("POST", "https://api.openai.com/v1/chat/completions")
        summary = shadow_eval._summarize_trace(trace, allow_openai=True)
        self.assertTrue(summary["allowed_methods_only"])
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertFalse(summary["allowed_methods_only"])

    def test_summarize_trace_rejects_unknown_service_and_method(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append({"method": "PUT", "path": "/x", "service": "richpanel"})
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertFalse(summary["allowed_methods_only"])
        trace = shadow_eval._HttpTrace()
        trace.entries.append({"method": "GET", "path": "/x", "service": "unknown"})
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertFalse(summary["allowed_methods_only"])

    def test_summarize_trace_aws_missing_operation(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {"method": "POST", "path": "/", "service": "aws_secretsmanager"}
        )
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertFalse(summary["allowed_methods_only"])
        self.assertEqual(summary.get("aws_missing_operations"), 1)

    def test_summarize_trace_aws_portal_bad_method(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {"method": "PUT", "path": "/federation/credentials", "service": "aws_portal"}
        )
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertFalse(summary["allowed_methods_only"])

    def test_summarize_trace_aws_portal_ok(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {"method": "GET", "path": "/federation/credentials", "service": "aws_portal"}
        )
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertTrue(summary["allowed_methods_only"])

    def test_summarize_trace_aws_non_post(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {
                "method": "GET",
                "path": "/",
                "service": "aws_secretsmanager",
                "operation": "GetSecretValue",
            }
        )
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertFalse(summary["allowed_methods_only"])

    def test_summarize_trace_aws_allowed_operation(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.entries.append(
            {
                "method": "POST",
                "path": "/",
                "service": "aws_secretsmanager",
                "operation": "GetSecretValue",
            }
        )
        summary = shadow_eval._summarize_trace(trace, allow_openai=False)
        self.assertTrue(summary["allowed_methods_only"])

    def test_extract_aws_operation_sources(self) -> None:
        class _Req:
            def __init__(self, **kwargs) -> None:
                for key, value in kwargs.items():
                    setattr(self, key, value)

        req = _Req(context={"operation_name": "GetSecretValue"})
        self.assertEqual(shadow_eval._extract_aws_operation(req), "GetSecretValue")

        req = _Req(headers={"X-Amz-Target": "secretsmanager.GetSecretValue"})
        self.assertEqual(shadow_eval._extract_aws_operation(req), "GetSecretValue")

        class _HeaderObj:
            def get(self, key, default=None):
                if key.lower() == "x-amz-target":
                    return "secretsmanager.GetSecretValue"
                return default

        req = _Req(headers=_HeaderObj())
        self.assertEqual(shadow_eval._extract_aws_operation(req), "GetSecretValue")

        req = _Req(body=b"Action=GetCallerIdentity&Version=2011-06-15")
        self.assertEqual(shadow_eval._extract_aws_operation(req), "GetCallerIdentity")

        req = _Req(data="Action=GetSessionToken&Version=2011-06-15")
        self.assertEqual(shadow_eval._extract_aws_operation(req), "GetSessionToken")

        req = _Req()
        self.assertIsNone(shadow_eval._extract_aws_operation(req))

    def test_resolve_shopify_secrets_client_no_profile(self) -> None:
        with mock.patch.dict(os.environ, _with_openai_env({}), clear=True):
            self.assertIsNone(shadow_eval._resolve_shopify_secrets_client())

    def test_resolve_shopify_secrets_client_with_profile(self) -> None:
        class _StubSession:
            def __init__(self, profile_name: str, region_name: str) -> None:
                self.profile_name = profile_name
                self.region_name = region_name

            def client(self, service_name: str, region_name=None):
                return {
                    "service": service_name,
                    "region": region_name,
                    "profile": self.profile_name,
                }

        class _StubBoto3:
            def Session(self, profile_name: str, region_name: str):
                return _StubSession(profile_name, region_name)

        env = {
            "SHOPIFY_ACCESS_TOKEN_PROFILE": "rp-admin-dev",
            "AWS_REGION": "us-east-2",
        }
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            with mock.patch.object(shadow_eval, "boto3", _StubBoto3()):
                client = shadow_eval._resolve_shopify_secrets_client()
        assert client is not None
        self.assertEqual(client["service"], "secretsmanager")
        self.assertEqual(client["profile"], "rp-admin-dev")
        self.assertEqual(client["region"], "us-east-2")

    def test_resolve_shopify_secrets_client_requires_boto3(self) -> None:
        env = {"SHOPIFY_ACCESS_TOKEN_PROFILE": "rp-admin-dev"}
        with mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            with mock.patch.object(shadow_eval, "boto3", None):
                with self.assertRaises(SystemExit):
                    shadow_eval._resolve_shopify_secrets_client()


class LiveReadonlyShadowEvalOpenAITests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._preflight_patch = mock.patch.object(
            shadow_eval,
            "run_secrets_preflight",
            return_value={"overall_status": "PASS"},
        )
        self._preflight_patch.start()

    def tearDown(self) -> None:
        self._preflight_patch.stop()
        super().tearDown()

    def test_openai_shadow_defaults_set(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            shadow_eval._apply_openai_shadow_eval_defaults()
            self.assertEqual(os.environ.get("MW_OPENAI_ROUTING_ENABLED"), "true")
            self.assertEqual(os.environ.get("MW_OPENAI_INTENT_ENABLED"), "true")
            self.assertEqual(os.environ.get("MW_OPENAI_SHADOW_ENABLED"), "true")
            self.assertEqual(os.environ.get("MW_ALLOW_NETWORK_READS"), "true")
            self.assertEqual(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"), "false")
            self.assertEqual(os.environ.get("OPENAI_ALLOW_NETWORK"), "true")

    def test_openai_gating_blockers_empty_when_enabled(self) -> None:
        env = {
            "MW_OPENAI_ROUTING_ENABLED": "true",
            "MW_OPENAI_INTENT_ENABLED": "true",
            "MW_OPENAI_SHADOW_ENABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
            "OPENAI_ALLOW_NETWORK": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(shadow_eval._openai_gating_blockers(), [])

    def test_emit_openai_banner_blocks_without_override(self) -> None:
        env = {"MW_OPENAI_ROUTING_ENABLED": "false"}
        with mock.patch.dict(os.environ, env, clear=True):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                with self.assertRaises(SystemExit):
                    shadow_eval._emit_openai_routing_banner(
                        allow_deterministic_only=False
                    )
            self.assertIn(
                "Results will undercount order-status",
                stream.getvalue(),
            )

    def test_emit_openai_banner_allows_with_override(self) -> None:
        env = {"MW_OPENAI_ROUTING_ENABLED": "false"}
        with mock.patch.dict(os.environ, env, clear=True):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                shadow_eval._emit_openai_routing_banner(
                    allow_deterministic_only=True
                )

    def test_aws_sdk_trace_capture_noop_when_wrapped(self) -> None:
        trace = shadow_eval._AwsSdkTrace([])
        trace._original_send = lambda *args, **kwargs: None
        trace.capture()
        self.assertIsNotNone(trace._original_send)

    def test_aws_sdk_trace_capture_handles_missing_botocore(self) -> None:
        trace = shadow_eval._AwsSdkTrace([])
        with mock.patch("builtins.__import__", side_effect=ImportError):
            trace.capture()
        self.assertFalse(trace.enabled)
        self.assertEqual(trace.error, "botocore_unavailable")

    def test_aws_sdk_trace_capture_records(self) -> None:
        entries: list[dict] = []
        trace = shadow_eval._AwsSdkTrace(entries)

        class _Req:
            method = "POST"
            url = "https://secretsmanager.us-east-2.amazonaws.com/"
            headers = {"X-Amz-Target": "secretsmanager.GetSecretValue"}
            body = b""
            context = {"operation_name": "GetSecretValue"}

        def _fake_send(self, request):
            return {"ok": True}

        endpoint_mod = types.ModuleType("botocore.endpoint")
        endpoint_mod.Endpoint = type("Endpoint", (), {"_send": _fake_send})
        botocore_mod = types.ModuleType("botocore")
        botocore_mod.endpoint = endpoint_mod
        fake_modules = {"botocore": botocore_mod, "botocore.endpoint": endpoint_mod}

        with mock.patch.dict(sys.modules, fake_modules):
            trace.capture()
            endpoint_mod.Endpoint._send(None, _Req())
            trace.stop()

        self.assertTrue(entries)
        self.assertEqual(entries[0]["service"], "aws_secretsmanager")
        self.assertEqual(entries[0]["operation"], "GetSecretValue")
        self.assertEqual(entries[0]["source"], "aws_sdk")

    def test_aws_sdk_trace_wrap_exception_path(self) -> None:
        trace = shadow_eval._AwsSdkTrace([])

        class _BadReq:
            method = "POST"
            headers = {}
            body = b""
            context = {}

            @property
            def url(self):
                raise ValueError("boom")

        def _fake_send(self, request):
            return {"ok": True}

        endpoint_mod = types.ModuleType("botocore.endpoint")
        endpoint_mod.Endpoint = type("Endpoint", (), {"_send": _fake_send})
        botocore_mod = types.ModuleType("botocore")
        botocore_mod.endpoint = endpoint_mod
        fake_modules = {"botocore": botocore_mod, "botocore.endpoint": endpoint_mod}

        with mock.patch.dict(sys.modules, fake_modules):
            trace.capture()
            endpoint_mod.Endpoint._send(None, _BadReq())
            trace.stop()

    def test_aws_sdk_trace_stop_handles_import_error(self) -> None:
        trace = shadow_eval._AwsSdkTrace([])
        trace._original_send = lambda *args, **kwargs: None
        with mock.patch("builtins.__import__", side_effect=ImportError):
            trace.stop()
        self.assertIsNone(trace._original_send)

    def test_delivery_estimate_present(self) -> None:
        self.assertFalse(shadow_eval._delivery_estimate_present("not a dict"))
        self.assertFalse(shadow_eval._delivery_estimate_present({}))
        self.assertTrue(
            shadow_eval._delivery_estimate_present({"eta_human": "2-4 days"})
        )

    def test_redact_tracking_number_various_lengths(self) -> None:
        # None/empty cases
        self.assertIsNone(shadow_eval._redact_tracking_number(None))
        self.assertIsNone(shadow_eval._redact_tracking_number(""))
        self.assertIsNone(shadow_eval._redact_tracking_number(123))  # type: ignore

        # Short tracking numbers (<=6 chars) should show only ***
        self.assertEqual(shadow_eval._redact_tracking_number("ABC"), "***")
        self.assertEqual(shadow_eval._redact_tracking_number("ABCDEF"), "***")

        # Medium tracking numbers (7-10 chars) show first 2 + last 2
        self.assertEqual(shadow_eval._redact_tracking_number("1234567"), "12***67")
        self.assertEqual(shadow_eval._redact_tracking_number("1234567890"), "12***90")

        # Long tracking numbers (>10 chars) show first 4 + last 3
        self.assertEqual(shadow_eval._redact_tracking_number("12345678901"), "1234***901")
        self.assertEqual(shadow_eval._redact_tracking_number("1ZV52E420840067015"), "1ZV5***015")

        # Whitespace handling - strips before redacting
        self.assertEqual(shadow_eval._redact_tracking_number("  1234567  "), "12***67")

        # Whitespace-only strings should return None (consistent with empty string)
        self.assertIsNone(shadow_eval._redact_tracking_number("   "))
        self.assertIsNone(shadow_eval._redact_tracking_number("  \t\n  "))

    def test_redact_date_various_formats(self) -> None:
        # None/empty cases
        self.assertIsNone(shadow_eval._redact_date(None))
        self.assertIsNone(shadow_eval._redact_date(""))
        self.assertIsNone(shadow_eval._redact_date(123))  # type: ignore

        # Full ISO date
        self.assertEqual(shadow_eval._redact_date("2026-01-24T10:30:00Z"), "2026-01-XX")
        self.assertEqual(shadow_eval._redact_date("2025-12-15T08:00:00+00:00"), "2025-12-XX")

        # Date only
        self.assertEqual(shadow_eval._redact_date("2026-01-24"), "2026-01-XX")

        # Malformed date (single part)
        self.assertEqual(shadow_eval._redact_date("2026"), "XXXX-XX-XX")

    def test_compute_eta_for_ticket_returns_none_when_missing_data(self) -> None:
        # Missing order_created
        result = shadow_eval._compute_eta_for_ticket(
            {"shipping_method": "Standard"},
            "2026-01-24T10:00:00Z"
        )
        self.assertIsNone(result)

        # Missing shipping_method
        result = shadow_eval._compute_eta_for_ticket(
            {"created_at": "2026-01-20T10:00:00Z"},
            "2026-01-24T10:00:00Z"
        )
        self.assertIsNone(result)

        # Empty dict
        result = shadow_eval._compute_eta_for_ticket({}, None)
        self.assertIsNone(result)

    def test_compute_eta_for_ticket_uses_shipping_method_name(self) -> None:
        # Should work with shipping_method_name field (alternative field name)
        with mock.patch.object(
            shadow_eval, "compute_delivery_estimate",
            return_value={
                "order_created_date": "2026-01-20",
                "inquiry_date": "2026-01-24",
                "normalized_method": "Standard",
                "elapsed_business_days": 3,
                "remaining_min_days": 0,
                "remaining_max_days": 4,
                "eta_human": "0-4 business days",
                "is_late": False,
                "bucket": "Standard",
            }
        ):
            result = shadow_eval._compute_eta_for_ticket(
                {
                    "order_created_at": "2026-01-20T10:00:00Z",
                    "shipping_method_name": "Standard Shipping",  # alternative field
                },
                "2026-01-24T10:00:00Z"
            )
            self.assertIsNotNone(result)
            self.assertEqual(result["shipping_method"], "Standard")
            self.assertEqual(result["order_date_redacted"], "2026-01-XX")

    def test_compute_eta_for_ticket_handles_empty_estimate(self) -> None:
        with mock.patch.object(
            shadow_eval, "compute_delivery_estimate", return_value=None
        ):
            result = shadow_eval._compute_eta_for_ticket(
                {
                    "created_at": "2026-01-20T10:00:00Z",
                    "shipping_method": "Standard",
                },
                "2026-01-24T10:00:00Z"
            )
            self.assertIsNone(result)

    def test_safe_error_redacts_exception_type(self) -> None:
        self.assertEqual(
            shadow_eval._safe_error(RuntimeError("boom"))["type"], "error"
        )
        self.assertEqual(
            shadow_eval._safe_error(shadow_eval.TransportError("boom"))["type"],
            "richpanel_error",
        )

    def test_fetch_ticket_uses_number_path_on_failure(self) -> None:
        class _SequenceClient:
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                if path.endswith("/v1/tickets/123"):
                    return _StubResponse({}, status_code=404)
                if path.endswith("/v1/tickets/number/123"):
                    return _StubResponse({"ticket": {"id": "t-123"}})
                return _StubResponse({}, status_code=404)

        result = shadow_eval._fetch_ticket(_SequenceClient(), "123")
        source_path = result.get("__source_path")
        self.assertTrue(source_path.startswith("/v1/tickets/number/"))
        self.assertNotIn("123", source_path)

    def test_fetch_ticket_raises_when_all_fail(self) -> None:
        class _FailClient:
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                raise shadow_eval.RichpanelRequestError("boom")

        with self.assertRaises(SystemExit) as ctx:
            shadow_eval._fetch_ticket(_FailClient(), "ticket-xyz")
        self.assertIn("redacted:", str(ctx.exception))

    def test_fetch_conversation_handles_error_status(self) -> None:
        class _ErrorClient:
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                return _StubResponse({}, status_code=500)

        result = shadow_eval._fetch_conversation(_ErrorClient(), "t-123")
        self.assertEqual(result, {})

    def test_fetch_conversation_handles_exception(self) -> None:
        class _BoomClient:
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                raise RuntimeError("boom")

        result = shadow_eval._fetch_conversation(_BoomClient(), "t-123")
        self.assertEqual(result, {})

    def test_fetch_conversation_flattens_conversation_wrapper(self) -> None:
        class _StubClient:
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                return _StubResponse(
                    {
                        "conversation": {"id": "c-1"},
                        "messages": [{"text": "hello"}],
                    }
                )

        result = shadow_eval._fetch_conversation(_StubClient(), "t-123")
        self.assertEqual(result.get("id"), "c-1")
        self.assertEqual(result.get("messages")[0]["text"], "hello")

    def test_fetch_conversation_handles_bad_json(self) -> None:
        class _BadJsonResponse(_StubResponse):
            def json(self) -> dict:
                raise ValueError("bad json")

        class _BadJsonClient:
            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                return _BadJsonResponse({}, status_code=200)

        result = shadow_eval._fetch_conversation(_BadJsonClient(), "t-123")
        self.assertEqual(result, {})

    def test_fetch_conversation_falls_back_to_messages(self) -> None:
        class _SequenceClient:
            def __init__(self) -> None:
                self.paths: list[str] = []

            def request(self, method: str, path: str, **kwargs) -> _StubResponse:
                self.paths.append(path)
                if path == "/api/v1/conversations/conv-1":
                    return _StubResponse({}, status_code=403)
                if path == "/v1/conversations/conv-1":
                    return _StubResponse({}, status_code=404)
                if path == "/api/v1/conversations/conv-1/messages":
                    return _StubResponse(
                        [{"sender_type": "customer", "body": "where is my order"}],
                        status_code=200,
                    )
                return _StubResponse({}, status_code=404)

        client = _SequenceClient()
        result = shadow_eval._fetch_conversation(
            client, "t-123", conversation_id="conv-1"
        )
        self.assertEqual(result.get("messages")[0]["body"], "where is my order")
        self.assertTrue(any("/api/v1/conversations/" in path for path in client.paths))
        source_path = result.get("__source_path", "")
        self.assertIn("/api/v1/conversations/", source_path)
        self.assertIn("/messages", source_path)

    def test_extract_order_payload_merges(self) -> None:
        ticket = {"order": {"order_id": "o-1"}, "__source_path": "/v1/tickets/1"}
        convo = {"orders": [{"tracking_number": "TN123"}]}
        merged = shadow_eval._extract_order_payload(ticket, convo)
        self.assertEqual(merged.get("order_id"), "o-1")
        self.assertEqual(merged.get("tracking_number"), "TN123")
        self.assertNotIn("__source_path", merged)

    def test_extract_order_payload_adds_order_number(self) -> None:
        ticket = {"comments": [{"plain_body": "Order #1158259"}]}
        convo: dict = {}
        merged = shadow_eval._extract_order_payload(ticket, convo)
        self.assertEqual(merged.get("order_number"), "1158259")

    def test_tracking_present_checks_fields(self) -> None:
        self.assertFalse(shadow_eval._tracking_present("not a dict"))
        self.assertTrue(
            shadow_eval._tracking_present({"tracking_number": "TN123"})
        )
        self.assertTrue(shadow_eval._tracking_present({"carrier_name": "UPS"}))

    def test_build_paths_create_dirs(self) -> None:
        with TemporaryDirectory() as tmpdir, mock.patch.object(
            shadow_eval, "ROOT", Path(tmpdir)
        ):
            report_path, report_md_path, trace_path = shadow_eval._build_report_paths(
                "RUN_TEST"
            )
            self.assertTrue(report_path.parent.exists())
            self.assertTrue(report_md_path.parent.exists())
            self.assertTrue(trace_path.parent.exists())

    def test_preflight_skips_when_boto3_missing(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(os.environ, _with_openai_env(env), clear=True):
            report_path = Path(tmpdir) / "report.json"
            argv = [
                "live_readonly_shadow_eval.py",
                "--sample-size",
                "1",
                "--allow-empty-sample",
                "--allow-non-prod",
                "--out",
                str(report_path),
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_build_shopify_client",
                return_value=SimpleNamespace(shop_domain="example.myshopify.com"),
            ), mock.patch.object(
                shadow_eval, "_resolve_shopify_secrets_client", return_value=None
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=[]
            ), mock.patch.object(shadow_eval, "run_secrets_preflight") as preflight, mock.patch.object(
                shadow_eval, "boto3", None
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            preflight.assert_not_called()

    def test_resolve_report_path_variants(self) -> None:
        with TemporaryDirectory() as tmpdir:
            report_file = Path(tmpdir) / "report.json"
            self.assertEqual(
                shadow_eval._resolve_report_path(str(report_file)), report_file
            )
            report_file_no_ext = Path(tmpdir) / "report"
            self.assertEqual(
                shadow_eval._resolve_report_path(str(report_file_no_ext)),
                report_file_no_ext.with_suffix(".json"),
            )
            self.assertEqual(
                shadow_eval._resolve_report_path(tmpdir),
                Path(tmpdir) / shadow_eval.CUSTOM_REPORT_FILENAME,
            )
            trailing = str(Path(tmpdir)) + os.sep
            self.assertEqual(
                shadow_eval._resolve_report_path(trailing),
                Path(tmpdir) / shadow_eval.CUSTOM_REPORT_FILENAME,
            )

    def test_resolve_output_paths_with_out_dir(self) -> None:
        with TemporaryDirectory() as tmpdir:
            report_path, summary_path, report_md_path, trace_path = (
                shadow_eval._resolve_output_paths(
                    "RUN_TEST", out_path=tmpdir, summary_md_out=None
                )
            )
            self.assertEqual(
                report_path.name, shadow_eval.CUSTOM_REPORT_FILENAME
            )
            self.assertEqual(
                summary_path.name, shadow_eval.CUSTOM_SUMMARY_JSON_FILENAME
            )
            self.assertEqual(
                report_md_path.name, shadow_eval.CUSTOM_SUMMARY_MD_FILENAME
            )
            self.assertEqual(
                trace_path.name, shadow_eval.CUSTOM_TRACE_FILENAME
            )
            custom_md = Path(tmpdir) / "custom.md"
            report_path, summary_path, report_md_path, trace_path = (
                shadow_eval._resolve_output_paths(
                    "RUN_TEST",
                    out_path=str(Path(tmpdir) / "report.json"),
                    summary_md_out=str(custom_md),
                )
            )
            self.assertEqual(report_md_path, custom_md)

    def test_resolve_output_paths_with_summary_override(self) -> None:
        with TemporaryDirectory() as tmpdir, mock.patch.object(
            shadow_eval, "ROOT", Path(tmpdir)
        ):
            custom_md = Path(tmpdir) / "alt_summary.md"
            report_path, summary_path, report_md_path, trace_path = (
                shadow_eval._resolve_output_paths(
                    "RUN_TEST", out_path=None, summary_md_out=str(custom_md)
                )
            )
            self.assertEqual(report_md_path, custom_md)
            self.assertIn("live_readonly_shadow_eval_summary_RUN_TEST.json", str(summary_path))

    def test_main_records_target_metadata_with_overrides(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            report_path = Path(tmpdir) / "report.json"
            summary_md_path = Path(tmpdir) / "summary.md"
            argv = [
                "live_readonly_shadow_eval.py",
                "--sample-size",
                "1",
                "--allow-empty-sample",
                "--allow-non-prod",
                "--env",
                "staging",
                "--region",
                "us-west-2",
                "--stack-name",
                "stack-1",
                "--shop-domain",
                "example.myshopify.com",
                "--out",
                str(report_path),
                "--summary-md-out",
                str(summary_md_path),
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_build_shopify_client",
                return_value=SimpleNamespace(shop_domain="example.myshopify.com"),
            ), mock.patch.object(
                shadow_eval, "_resolve_shopify_secrets_client", return_value=None
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=[]
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            target = payload["target"]
            self.assertEqual(target["env"], "staging")
            self.assertEqual(target["region"], "us-west-2")
            self.assertEqual(target["stack_name"], "stack-1")
            self.assertEqual(
                target["shop_domain"],
                shadow_eval._redact_shop_domain("example.myshopify.com"),
            )
            self.assertIn("tracking_or_eta_available", payload["counts"])

    def test_main_uses_recent_sample_when_no_ticket_id(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        plan = SimpleNamespace(
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {
                        "order_summary": {"order_id": "order-123"},
                        "delivery_estimate": {"eta_human": "2-4 days"},
                    },
                }
            ],
            routing=SimpleNamespace(
                intent="order_status_tracking",
                department="Email Support Team",
                reason="stubbed",
            ),
            mode="automation_candidate",
            reasons=["stubbed"],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            argv = [
                "live_readonly_shadow_eval.py",
                "--sample-size",
                "2",
                "--allow-non-prod",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=["t-1", "t-2"]
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", return_value={}
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["sample_mode"], "recent")
            self.assertEqual(payload["counts"]["tickets_scanned"], 2)
            self.assertTrue(payload["tickets"][0]["ticket_id_redacted"].startswith("redacted:"))
            self.assertEqual(
                payload["tickets"][0]["routing"]["intent"], "order_status_tracking"
            )
            self.assertIn("order_id_present", payload["tickets"][0])
            self.assertIn("order_context_missing", payload["tickets"][0])
            self.assertTrue(payload["tickets"][0]["order_matched"])

    def test_non_explicit_mode_performs_shopify_lookup(self) -> None:
        """Test that sample_mode='recent' performs Shopify lookup for metrics."""
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        # Plan with NO order_summary to verify order_matched=False in non-explicit mode
        plan = SimpleNamespace(
            actions=[],  # No order_status_draft_reply action
            routing=SimpleNamespace(
                intent="unknown_other",
                department="Email Support Team",
                reason="stubbed",
            ),
            mode="none",
            reasons=["stubbed"],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            lookup_calls = []

            def mock_lookup(*args, **kwargs):
                lookup_calls.append(True)
                return {}

            argv = [
                "live_readonly_shadow_eval.py",
                "--sample-size",
                "1",
                "--allow-non-prod",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=["t-1"]
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", side_effect=mock_lookup
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            # Verify lookup_order_summary was called in non-explicit mode
            self.assertEqual(len(lookup_calls), 1)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["sample_mode"], "recent")
            # With no order_summary and an empty Shopify summary, order_matched should be False
            self.assertFalse(payload["tickets"][0]["order_matched"])
            # Shopify fields are populated from the lookup summary
            self.assertIn("shopify_tracking_number", payload["tickets"][0])
            self.assertIn("order_resolution", payload["tickets"][0])

    def test_main_runs_with_stubbed_client(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
            "SHOPIFY_OUTBOUND_ENABLED": "true",
        }
        plan = SimpleNamespace(
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {
                        "order_summary": {
                            "order_id": "order-123",
                            "tracking_number": "TN123",
                        },
                        "delivery_estimate": {"eta_human": "2-4 days"},
                        "draft_reply": {"body": "stubbed"},
                    },
                }
            ],
            routing=SimpleNamespace(
                intent="order_status_tracking",
                department="Email Support Team",
                reason="stubbed",
            ),
            mode="automation_candidate",
            reasons=["stubbed"],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            captured: dict[str, dict] = {}
            def _capture_event(payload: dict) -> SimpleNamespace:
                captured["payload"] = payload["payload"]
                return SimpleNamespace()
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--allow-non-prod",
                "--shop-domain",
                "example.myshopify.com",
                "--shopify-probe",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(artifact_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", side_effect=_capture_event
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval,
                "lookup_order_summary",
                return_value={
                    "order_resolution": {
                        "resolvedBy": "probe",
                        "confidence": "high",
                        "reason": "test",
                    }
                },
            ), mock.patch.object(
                shadow_eval,
                "_probe_shopify",
                return_value={"status_code": 200, "dry_run": False, "ok": True},
            ):
                result = shadow_eval.main()
                self.assertEqual(result, 0)
                self.assertTrue(trace_path.exists())
                self.assertTrue(artifact_path.exists())
                self.assertTrue(report_md_path.exists())
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                self.assertTrue(payload["shopify_probe"]["enabled"])
                self.assertTrue(payload["shopify_probe"]["ok"])
                self.assertEqual(
                    captured["payload"]["conversation_id"], "conv-123"
                )
                self.assertEqual(
                    payload["tickets"][0]["routing"]["intent"], "order_status_tracking"
                )
            self.assertEqual(
                payload["tickets"][0]["order_resolution"]["resolvedBy"], "probe"
            )
            self.assertIn("order_created_at_present", payload["tickets"][0])
            self.assertIn(
                "tracking_or_shipping_method_present", payload["tickets"][0]
            )

    def test_main_raises_when_no_ticket_refs(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--allow-non-prod"]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=[]
            ):
                with self.assertRaises(SystemExit):
                    shadow_eval.main()

    def test_listing_failure_raises_without_allow_empty(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--sample-size", "1", "--allow-non-prod"]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval,
                "_fetch_recent_ticket_refs",
                side_effect=SystemExit("Ticket listing failed: status 403 dry_run=False"),
            ):
                with self.assertRaises(SystemExit):
                    shadow_eval.main()

    def test_main_rejects_conflicting_sample_size(self) -> None:
        argv = [
            "live_readonly_shadow_eval.py",
            "--sample-size",
            "1",
            "--max-tickets",
            "2",
            "--allow-deterministic-only",
        ]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as ctx:
                shadow_eval.main()
        self.assertIn("Use --sample-size or --max-tickets", str(ctx.exception))

    def test_allow_empty_sample_on_listing_failure(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "live_readonly_shadow_eval_summary_RUN_TEST.json"
            argv = [
                "live_readonly_shadow_eval.py",
                "--sample-size",
                "1",
                "--allow-non-prod",
                "--allow-empty-sample",
                "--run-id",
                "RUN_TEST",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval,
                "_fetch_recent_ticket_refs",
                side_effect=SystemExit("Ticket listing failed: status 403 dry_run=False"),
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["counts"]["tickets_scanned"], 0)
            self.assertIn("ticket_listing_403", payload["run_warnings"])
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertIn("ticket_listing_403", summary["run_warnings"])

    def test_main_records_shopify_lookup_error(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "t-1", "--allow-non-prod"]
            shopify_error = shadow_eval.ShopifyRequestError(
                "boom", response=SimpleNamespace(status_code=401)
            )
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=SimpleNamespace(actions=[])
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", side_effect=shopify_error
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 1)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["tickets"][0]["failure_reason"], "shopify_401")

    def test_main_records_richpanel_request_error(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "t-1", "--allow-non-prod"]
            richpanel_error = shadow_eval.RichpanelRequestError(
                "boom", response=SimpleNamespace(status_code=401)
            )
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_ticket", side_effect=richpanel_error
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 1)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["tickets"][0]["failure_reason"], "richpanel_401")

    def test_allows_ticket_fetch_failure_when_flag_set(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = [
                "live_readonly_shadow_eval.py",
                "--sample-size",
                "1",
                "--allow-non-prod",
                "--allow-ticket-fetch-failures",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=["t-1"]
            ), mock.patch.object(
                shadow_eval,
                "_fetch_ticket",
                side_effect=SystemExit("Ticket lookup failed for redacted:t-1: boom"),
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("ticket_fetch_failed", payload["run_warnings"])
            self.assertEqual(payload["tickets"][0]["failure_reason"], "ticket_fetch_failed")

    def test_main_warns_when_sample_reduced(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        plan = SimpleNamespace(
            actions=[],
            routing=SimpleNamespace(intent="unknown", department="Email", reason="stubbed"),
            mode="none",
            reasons=[],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--sample-size", "2", "--allow-non-prod"]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=["t-1"]
            ), mock.patch.object(
                shadow_eval, "_fetch_ticket", return_value={"id": "t-1"}
            ), mock.patch.object(
                shadow_eval, "_fetch_conversation", return_value={}
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", return_value={}
            ):
                with self.assertLogs("readonly_shadow_eval", level="WARNING") as logs:
                    shadow_eval.main()
                self.assertIn("Sample size reduced", "\n".join(logs.output))

    def test_main_records_error_when_ticket_processing_fails(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--sample-size", "1", "--allow-non-prod"]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=["t-1"]
            ), mock.patch.object(
                shadow_eval, "_fetch_ticket", side_effect=RuntimeError("boom")
            ):
                result = shadow_eval.main()
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 1)
            self.assertEqual(payload["counts"]["errors"], 1)

    def test_allow_ticket_fetch_failures_appends_once(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-1",
                "--allow-non-prod",
                "--allow-ticket-fetch-failures",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_ticket", side_effect=RuntimeError("boom")
            ):
                result = shadow_eval.main()
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 1)
            self.assertEqual(len(payload["tickets"]), 1)
            self.assertEqual(
                payload["tickets"][0]["failure_reason"],
                "richpanel_ticket_fetch_failed",
            )

    def test_request_trace_and_skip_conversations(self) -> None:
        class _TraceClient:
            base_url = "https://api.richpanel.com"
            api_key_secret_id = "rp-mw/dev/richpanel/api_key"

            def _load_api_key(self) -> str:
                return "trace-key"

            def clear_request_trace(self) -> None:
                return None

            def get_request_trace(self) -> list[dict]:
                return [
                    {
                        "timestamp": 1.0,
                        "path": "/v1/tickets",
                        "retry_after": 1,
                        "retry_delay_seconds": 2,
                    }
                ]

        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        plan = SimpleNamespace(
            actions=[],
            routing=SimpleNamespace(
                intent="unknown_other",
                department="Email Support Team",
                reason="stubbed",
            ),
            mode="none",
            reasons=["stubbed"],
        )
        ticket_payload = {
            "id": "t-123",
            "conversation_id": "conv-123",
            "created_at": "2026-01-01T00:00:00Z",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--allow-non-prod",
                "--request-trace",
                "--skip-conversations",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_TraceClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_ticket", return_value=ticket_payload
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", return_value={}
            ):
                result = shadow_eval.main()
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(payload["conversation_mode"], "skipped")
            self.assertTrue(payload.get("richpanel_request_burst"))
            self.assertEqual(
                payload.get("richpanel_retry_after_validation", {}).get("checked"), 1
            )
            self.assertTrue(payload.get("richpanel_identity"))

    def test_main_reraises_system_exit_in_ticket_loop(self) -> None:
        env = {
            "MW_ENV": "prod",
            "SHOPIFY_SHOP_DOMAIN": "test-shop.myshopify.com",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "t-1"]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=_StubClient()
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(report_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "_fetch_ticket", side_effect=SystemExit("boom")
            ):
                with self.assertRaises(SystemExit):
                    shadow_eval.main()

    def test_main_records_probe_error(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
            "SHOPIFY_OUTBOUND_ENABLED": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--allow-non-prod",
                "--shop-domain",
                "example.myshopify.com",
                "--shopify-probe",
            ]
            plan = SimpleNamespace(
                actions=[],
                routing=SimpleNamespace(
                    intent="unknown", department="Email Support Team", reason="stubbed"
                ),
                mode="automation_candidate",
                reasons=["stubbed"],
            )
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(artifact_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", return_value={}
            ), mock.patch.object(
                shadow_eval,
                "_probe_shopify",
                return_value={"status_code": 403, "dry_run": False, "ok": False},
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["shopify_probe"]["error"]["type"], "shopify_error")

    def test_order_resolution_none_handling(self) -> None:
        """Test that order_resolution being None (not just absent) is handled safely."""
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        plan = SimpleNamespace(
            actions=[],
            routing=SimpleNamespace(
                intent="unknown", department="Email Support Team", reason="stubbed"
            ),
            mode="automation_candidate",
            reasons=["stubbed"],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--allow-non-prod",
            ]
            # Return order_resolution as None (not absent, but explicitly None)
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(artifact_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval,
                "lookup_order_summary",
                return_value={"order_resolution": None, "order_id": "123"},  # None value
            ):
                result = shadow_eval.main()
            # Should not crash and should return successfully
            self.assertEqual(result, 0)
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            # order_matched should be False when order_resolution is None
            self.assertFalse(payload["tickets"][0]["order_matched"])

    def test_eta_available_with_shipping_method_name(self) -> None:
        """Test that eta_available checks shipping_method_name field too."""
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
        }
        plan = SimpleNamespace(
            actions=[],
            routing=SimpleNamespace(
                intent="unknown", department="Email Support Team", reason="stubbed"
            ),
            mode="automation_candidate",
            reasons=["stubbed"],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--allow-non-prod",
            ]
            # Return shipping_method_name instead of shipping_method
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(artifact_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval,
                "lookup_order_summary",
                return_value={
                    "order_id": "123",
                    "created_at": "2026-01-20T10:00:00Z",  # has order date
                    "shipping_method_name": "Standard Shipping",  # alternative field
                },
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            # eta_available should be True because we have order date + shipping_method_name
            self.assertTrue(payload["tickets"][0]["eta_available"])

    def test_main_records_probe_exception(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "false",
            "SHOPIFY_OUTBOUND_ENABLED": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, _with_openai_env(env), clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
            summary_path = Path(tmpdir) / "summary.json"
            stub_client = _StubClient()
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--allow-non-prod",
                "--shop-domain",
                "example.myshopify.com",
                "--shopify-probe",
            ]
            plan = SimpleNamespace(
                actions=[],
                routing=SimpleNamespace(
                    intent="unknown", department="Email Support Team", reason="stubbed"
                ),
                mode="automation_candidate",
                reasons=["stubbed"],
            )
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_resolve_output_paths",
                return_value=(artifact_path, summary_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "lookup_order_summary", return_value={}
            ), mock.patch.object(
                shadow_eval,
                "_probe_shopify",
                side_effect=shadow_eval.ShopifyRequestError("boom"),
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["shopify_probe"]["error"]["type"], "shopify_error")


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        LiveReadonlyShadowEvalGuardTests
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            LiveReadonlyShadowEvalHelpersTests
        )
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
