from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import live_readonly_shadow_eval as shadow_eval  # noqa: E402


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
                    "order": {"order_id": "order-123", "tracking_number": "TN123"},
                    "customer": {"email": "customer@example.com", "name": "Test User"},
                }
            }
            return _StubResponse(payload)
        if path.startswith("/api/v1/conversations/"):
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
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "123"]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as ctx:
                    shadow_eval.main()
        self.assertIn("RICHPANEL_WRITE_DISABLED", str(ctx.exception))


class LiveReadonlyShadowEvalHelpersTests(unittest.TestCase):
    def test_require_prod_environment_blocks_non_prod(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit):
                shadow_eval._require_prod_environment(allow_non_prod=False)
            self.assertEqual(
                shadow_eval._require_prod_environment(allow_non_prod=True), "dev"
            )

    def test_resolve_env_name_defaults_to_local(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(shadow_eval._resolve_env_name(), "local")

    def test_resolve_env_name_prefers_richpanel_env(self) -> None:
        env = {"RICHPANEL_ENV": "Staging", "MW_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(shadow_eval._resolve_env_name(), "staging")

    def test_resolve_richpanel_base_url_override(self) -> None:
        env = {"RICHPANEL_API_BASE_URL": "https://api.richpanel.com/"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                shadow_eval._resolve_richpanel_base_url(),
                "https://api.richpanel.com",
            )

    def test_require_env_flags_success(self) -> None:
        env = {
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            applied = shadow_eval._require_env_flags("test")
        self.assertEqual(applied, shadow_eval.REQUIRED_FLAGS)

    def test_require_env_flag_mismatch_raises(self) -> None:
        env = {"RICHPANEL_WRITE_DISABLED": "false"}
        with mock.patch.dict(os.environ, env, clear=True):
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

    def test_is_prod_target_detects_env(self) -> None:
        env = {"MW_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url=shadow_eval.PROD_RICHPANEL_BASE_URL,
                richpanel_secret_id=None,
            )
        self.assertTrue(result)

    def test_is_prod_target_detects_prod_key_and_base(self) -> None:
        env = {"PROD_RICHPANEL_API_KEY": "token-value"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url=shadow_eval.PROD_RICHPANEL_BASE_URL,
                richpanel_secret_id=None,
            )
        self.assertTrue(result)

    def test_is_prod_target_false_for_non_prod(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, env, clear=True):
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
        convo = {
            "messages": [
                {"sender_type": "agent", "body": "ignore"},
                {"sender_type": "customer", "body": "need tracking"},
            ]
        }
        message = shadow_eval._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "need tracking")

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

    def test_require_env_flag_missing_raises(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
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
        trace.assert_get_only(context="test", trace_path=Path("trace.json"))
        self.assertEqual(trace.entries[0]["method"], "GET")

        trace.record("POST", "https://api.richpanel.com/v1/tickets/123")
        with self.assertRaises(SystemExit):
            trace.assert_get_only(context="test", trace_path=Path("trace.json"))

    def test_http_trace_service_mapping(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://shop.myshopify.com/admin/api/2024-01/orders/1")
        trace.record("GET", "https://ssapi.shipstation.com/shipments")
        self.assertEqual(trace.entries[0]["service"], "shopify")
        self.assertEqual(trace.entries[1]["service"], "shipstation")

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

    def test_summarize_trace_counts(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://api.richpanel.com/v1/tickets/123")
        trace.record("HEAD", "https://api.richpanel.com/v1/tickets/123")
        summary = shadow_eval._summarize_trace(trace)
        self.assertEqual(summary["total_requests"], 2)
        self.assertTrue(summary["allowed_methods_only"])
        self.assertEqual(summary["methods"].get("GET"), 1)

    def test_delivery_estimate_present(self) -> None:
        self.assertFalse(shadow_eval._delivery_estimate_present("not a dict"))
        self.assertTrue(
            shadow_eval._delivery_estimate_present({"eta_human": "2-4 days"})
        )

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

    def test_extract_order_payload_merges(self) -> None:
        ticket = {"order": {"order_id": "o-1"}, "__source_path": "/v1/tickets/1"}
        convo = {"orders": [{"tracking_number": "TN123"}]}
        merged = shadow_eval._extract_order_payload(ticket, convo)
        self.assertEqual(merged.get("order_id"), "o-1")
        self.assertEqual(merged.get("tracking_number"), "TN123")
        self.assertNotIn("__source_path", merged)

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

    def test_main_uses_recent_sample_when_no_ticket_id(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
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
            os.environ, env, clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            report_path = Path(tmpdir) / "report.json"
            report_md_path = Path(tmpdir) / "report.md"
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
                "_build_report_paths",
                return_value=(report_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval, "_fetch_recent_ticket_refs", return_value=["t-1", "t-2"]
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["sample_mode"], "recent")
            self.assertEqual(payload["counts"]["tickets_scanned"], 2)
            self.assertTrue(payload["tickets"][0]["ticket_id_redacted"].startswith("redacted:"))

    def test_main_runs_with_stubbed_client(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
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
            os.environ, env, clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
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
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval,
                "_build_report_paths",
                return_value=(artifact_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
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

    def test_main_records_probe_error(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "SHOPIFY_OUTBOUND_ENABLED": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
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
                "_build_report_paths",
                return_value=(artifact_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ), mock.patch.object(
                shadow_eval,
                "_probe_shopify",
                return_value={"status_code": 403, "dry_run": False, "ok": False},
            ):
                result = shadow_eval.main()
            self.assertEqual(result, 0)
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["shopify_probe"]["error"]["type"], "shopify_error")

    def test_main_records_probe_exception(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "SHOPIFY_OUTBOUND_ENABLED": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            report_md_path = Path(tmpdir) / "report.md"
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
                "_build_report_paths",
                return_value=(artifact_path, report_md_path, trace_path),
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
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
