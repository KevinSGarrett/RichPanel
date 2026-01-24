from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import shadow_order_status as shadow  # noqa: E402


class _StubResponse:
    def __init__(self, payload: dict, status_code: int = 200, dry_run: bool = False):
        self.status_code = status_code
        self.dry_run = dry_run
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _GuardedRichpanelClient:
    def __init__(self, ticket_payload: dict, convo_payload: dict):
        self.ticket_payload = ticket_payload
        self.convo_payload = convo_payload
        self.methods: list[str] = []

    def request(self, method: str, path: str, **kwargs) -> _StubResponse:
        self.methods.append(method.upper())
        if method.upper() not in {"GET", "HEAD"}:
            raise AssertionError("Write method called in shadow mode")
        if path.startswith("/v1/tickets/"):
            return _StubResponse({"ticket": self.ticket_payload})
        if path.startswith("/api/v1/conversations/"):
            return _StubResponse(self.convo_payload)
        return _StubResponse({}, status_code=404)


class _GuardedShopifyClient:
    def __init__(self):
        self.called = False

    def get_order(self, *args, **kwargs):
        self.called = True
        raise AssertionError("Shopify should not be called for payload-first summary")


class _StubShopifyResponse:
    def __init__(self, payload: dict, status_code: int = 200, dry_run: bool = False):
        self.status_code = status_code
        self.dry_run = dry_run
        self._payload = payload

    def json(self) -> dict:
        return self._payload


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


class ShadowOrderStatusGuardTests(unittest.TestCase):
    def test_require_env_flag_missing_and_mismatch(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                shadow._require_env_flag("RICHPANEL_READ_ONLY", "true", context="test")
        with mock.patch.dict(os.environ, {"RICHPANEL_READ_ONLY": "false"}, clear=True):
            with self.assertRaises(SystemExit):
                shadow._require_env_flag("RICHPANEL_READ_ONLY", "true", context="test")
    def test_requires_readonly_flags(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("RICHPANEL_READ_ONLY", str(ctx.exception))

    def test_requires_confirm_flag(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=False)
        self.assertIn("confirm-live-readonly", str(ctx.exception))

    def test_whitespace_ticket_id_rejected(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            out_path = Path(tmpdir) / "out.json"
            argv = [
                "shadow_order_status.py",
                "--ticket-id",
                "   ",
                "--out",
                str(out_path),
                "--confirm-live-readonly",
            ]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as ctx:
                    shadow.main()
        self.assertIn("ticket-id", str(ctx.exception))

    def test_env_must_be_staging_or_prod(self) -> None:
        env = {
            "RICHPANEL_ENV": "dev",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("staging", str(ctx.exception))

    def test_requires_network_read_flag(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("MW_ALLOW_NETWORK_READS", str(ctx.exception))

    def test_requires_richpanel_env(self) -> None:
        env = {
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("RICHPANEL_ENV", str(ctx.exception))

    def test_resolve_env_name_prefers_richpanel_env(self) -> None:
        env = {"RICHPANEL_ENV": "Staging", "RICH_PANEL_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(shadow._resolve_env_name(), "staging")

    def test_resolve_env_name_fallback(self) -> None:
        env = {"RICH_PANEL_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(shadow._resolve_env_name(), "prod")

    def test_shopify_secret_override_guard(self) -> None:
        env = {
            "SHOPIFY_ACCESS_TOKEN_OVERRIDE": "tok",
            "SHOPIFY_ACCESS_TOKEN_SECRET_ID": "rp-mw/staging/shopify/admin_api_token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._resolve_shopify_secret_id("staging")
        self.assertIn("SHOPIFY_ACCESS_TOKEN_OVERRIDE", str(ctx.exception))

    def test_shopify_secret_id_validation(self) -> None:
        env = {"SHOPIFY_ACCESS_TOKEN_SECRET_ID": "rp-mw/staging/shopify/admin_api_token"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                shadow._resolve_shopify_secret_id("staging"),
                "rp-mw/staging/shopify/admin_api_token",
            )
        env = {"SHOPIFY_ACCESS_TOKEN_SECRET_ID": "rp-mw/staging/other/token"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit):
                shadow._resolve_shopify_secret_id("staging")


class ShadowOrderStatusHelperTests(unittest.TestCase):
    def test_fetch_recent_ticket_refs_success(self) -> None:
        payload = {
            "tickets": [
                {"id": "t-1"},
                {"conversation_no": "1001"},
                {"id": "t-1"},
            ]
        }
        client = _ListingClient(payload)
        results = shadow._fetch_recent_ticket_refs(
            client, sample_size=2, list_path="/v1/tickets"
        )
        self.assertEqual(results, ["t-1", "1001"])

    def test_fetch_recent_ticket_refs_errors_on_status(self) -> None:
        client = _ListingClient({}, status_code=500)
        with self.assertRaises(SystemExit):
            shadow._fetch_recent_ticket_refs(
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
        results = shadow._fetch_recent_ticket_refs(
            client, sample_size=2, list_path="/v1/tickets"
        )
        self.assertEqual(results, ["c-1", "1002"])
        self.assertEqual(
            client.paths,
            ["/v1/tickets", "/api/v1/conversations", "/v1/conversations"],
        )

    def test_safe_error_redacts_exception_type(self) -> None:
        self.assertEqual(shadow._safe_error(RuntimeError("boom"))["type"], "error")
        self.assertEqual(
            shadow._safe_error(shadow.TransportError("boom"))["type"],
            "richpanel_error",
        )


class ShadowOrderStatusRedactionTests(unittest.TestCase):
    def test_customer_presence(self) -> None:
        ticket = {"customer": {"email": "a@example.com", "name": "Alice"}}
        convo = {"customer_profile": {"phone": "555-1212", "address": "123 Main"}}
        presence = shadow._extract_customer_presence(ticket, convo)
        self.assertTrue(presence["email_present"])
        self.assertTrue(presence["name_present"])
        self.assertTrue(presence["phone_present"])
        self.assertTrue(presence["address_present"])

    def test_redact_path_variants(self) -> None:
        self.assertEqual(shadow._redact_path(""), "/")
        redacted = shadow._redact_path("/v1/tickets/91608")
        self.assertIn("/v1/tickets/", redacted)
        self.assertNotIn("91608", redacted)
        redacted = shadow._redact_path("/api/v1/orders/ABC")
        self.assertIn("/ABC", redacted)
        self.assertNotIn("redacted:", redacted)

    def test_tracking_present(self) -> None:
        self.assertFalse(shadow._tracking_present("not a dict"))
        self.assertTrue(shadow._tracking_present({"tracking_number": "TN"}))
        self.assertTrue(shadow._tracking_present({"carrier_name": "UPS"}))


class ShadowOrderStatusTraceTests(unittest.TestCase):
    def test_http_trace_blocks_non_get(self) -> None:
        trace = shadow._HttpTrace()
        trace.record("GET", "https://api.richpanel.com/v1/tickets/123")
        trace.record("POST", "https://api.richpanel.com/v1/tickets/123")
        with self.assertRaises(SystemExit):
            trace.assert_read_only(
                allow_openai=False, trace_path=Path("trace.json")
            )

    def test_http_trace_allows_openai_when_enabled(self) -> None:
        trace = shadow._HttpTrace()
        trace.record("POST", "https://api.openai.com/v1/chat/completions")
        trace.assert_read_only(allow_openai=True, trace_path=Path("trace.json"))

    def test_http_trace_unknown_service(self) -> None:
        trace = shadow._HttpTrace()
        trace.record("GET", "https://example.com/anything")
        with self.assertRaises(SystemExit):
            trace.assert_read_only(allow_openai=False, trace_path=Path("trace.json"))

    def test_http_trace_capture_restores_urlopen(self) -> None:
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

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen) as patched:
            trace = shadow._HttpTrace().capture()
            request = shadow.urllib.request.Request(
                "https://api.richpanel.com/v1/tickets/123", method="GET"
            )
            shadow.urllib.request.urlopen(request)
            trace.stop()
            self.assertIs(shadow.urllib.request.urlopen, patched)
        self.assertTrue(calls)
        self.assertTrue(trace.entries)


class ShadowOrderStatusNoWriteTests(unittest.TestCase):
    def test_run_ticket_is_read_only(self) -> None:
        ticket = {
            "id": "t-1",
            "created_at": "2024-01-02T00:00:00Z",
            "customer_message": "where is my order",
            "order": {
                "order_id": "o-1",
                "tracking_number": "TN123456",
                "carrier": "UPS",
                "created_at": "2024-01-01T00:00:00Z",
                "shipping_method": "Standard",
            },
            "customer": {"email": "customer@example.com", "name": "Test User"},
        }
        convo = {}
        rp_client = _GuardedRichpanelClient(ticket, convo)
        shopify_client = _GuardedShopifyClient()
        routing = SimpleNamespace(
            intent="order_status_tracking",
            department="Email Support Team",
            reason="stubbed",
        )
        routing_artifact = SimpleNamespace(
            primary_source="deterministic",
            llm_suggestion={"confidence": 0.9, "model": "gpt-test"},
        )
        with mock.patch.object(
            shadow, "compute_dual_routing", return_value=(routing, routing_artifact)
        ):
            result = shadow.run_ticket(
                "t-1",
                richpanel_client=rp_client,
                shopify_client=shopify_client,
                allow_network=True,
                outbound_enabled=False,
                rewrite_enabled=False,
            )
        self.assertTrue(all(method in {"GET", "HEAD"} for method in rp_client.methods))
        self.assertFalse(shopify_client.called)
        self.assertTrue(result["order_status"]["tracking_present"])
        self.assertTrue(result["customer_presence"]["name_present"])

    def test_run_ticket_non_order_status(self) -> None:
        ticket = {"customer_message": "refund my order"}
        rp_client = _GuardedRichpanelClient(ticket, {})
        shopify_client = _GuardedShopifyClient()
        routing = SimpleNamespace(
            intent="refund_request",
            department="Returns Admin",
            reason="stubbed",
        )
        routing_artifact = SimpleNamespace(
            primary_source="deterministic",
            llm_suggestion={"confidence": 0.2, "model": "gpt-test"},
        )
        with mock.patch.object(
            shadow, "compute_dual_routing", return_value=(routing, routing_artifact)
        ):
            result = shadow.run_ticket(
                "t-2",
                richpanel_client=rp_client,
                shopify_client=shopify_client,
                allow_network=False,
                outbound_enabled=False,
                rewrite_enabled=False,
            )
        self.assertFalse(result["order_status"]["is_order_status"])
        self.assertEqual(result["order_status"]["skipped_reason"], "route_not_order_status")

    def test_run_ticket_openai_evidence(self) -> None:
        ticket = {
            "customer_message": "where is my order",
            "order": {"tracking_number": "TN1234", "carrier": "UPS"},
        }
        rp_client = _GuardedRichpanelClient(ticket, {})
        shopify_client = _GuardedShopifyClient()
        routing = SimpleNamespace(
            intent="order_status_tracking",
            department="Email Support Team",
            reason="stubbed",
        )
        routing_artifact = SimpleNamespace(
            primary_source="deterministic",
            llm_suggestion={"confidence": 0.8, "model": "gpt-test"},
        )
        rewrite_result = shadow.ReplyRewriteResult(
            body="rewritten",
            rewritten=True,
            reason="ok",
            model="gpt-test",
            confidence=0.9,
            dry_run=False,
            fingerprint="fp",
            llm_called=True,
            response_id="resp-1",
        )
        with mock.patch.object(
            shadow, "compute_dual_routing", return_value=(routing, routing_artifact)
        ), mock.patch.object(
            shadow, "rewrite_reply", return_value=rewrite_result
        ):
            result = shadow.run_ticket(
                "t-3",
                richpanel_client=rp_client,
                shopify_client=shopify_client,
                allow_network=True,
                outbound_enabled=True,
                rewrite_enabled=True,
            )
        evidence = result["order_status"]["openai_rewrite"]
        self.assertTrue(evidence["rewrite_attempted"])
        self.assertEqual(evidence["response_id"], "resp-1")

    def test_draft_reply_type_no_tracking(self) -> None:
        ticket = {
            "customer_message": "where is my order",
            "order": {"order_id": "o-1"},
        }
        rp_client = _GuardedRichpanelClient(ticket, {})
        shopify_client = _GuardedShopifyClient()
        routing = SimpleNamespace(
            intent="order_status_tracking",
            department="Email Support Team",
            reason="stubbed",
        )
        routing_artifact = SimpleNamespace(
            primary_source="deterministic",
            llm_suggestion={"confidence": 0.1, "model": "gpt-test"},
        )
        with mock.patch.object(
            shadow, "compute_dual_routing", return_value=(routing, routing_artifact)
        ):
            result = shadow.run_ticket(
                "t-4",
                richpanel_client=rp_client,
                shopify_client=shopify_client,
                allow_network=False,
                outbound_enabled=False,
                rewrite_enabled=False,
            )
        self.assertEqual(result["order_status"]["draft_reply_type"], "no_tracking")

    def test_build_openai_evidence(self) -> None:
        rewrite_result = shadow.ReplyRewriteResult(
            body="x",
            rewritten=False,
            reason="dry_run",
            model="gpt-test",
            confidence=0.0,
            dry_run=True,
            fingerprint="fp",
            llm_called=False,
            response_id=None,
        )
        evidence = shadow._build_openai_evidence(rewrite_result)
        self.assertFalse(evidence["rewrite_attempted"])
        self.assertEqual(evidence["model"], "gpt-test")

    def test_build_route_info(self) -> None:
        routing = SimpleNamespace(
            intent="order_status_tracking",
            department="Email Support Team",
            reason="stubbed",
        )
        artifact = SimpleNamespace(
            primary_source="deterministic",
            llm_suggestion={"confidence": 0.9, "model": "gpt-test"},
        )
        info = shadow._build_route_info(routing, artifact)
        self.assertEqual(info["intent"], "order_status_tracking")
        self.assertEqual(info["primary_source"], "deterministic")
        artifact = SimpleNamespace(primary_source="deterministic")
        info = shadow._build_route_info(routing, artifact)
        self.assertIsNone(info["confidence"])

    def test_extract_latest_customer_message(self) -> None:
        convo = {
            "messages": [
                {"sender_type": "agent", "body": "ignore"},
                {"sender_type": "customer", "body": "need tracking"},
            ]
        }
        message = shadow._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "need tracking")

        convo = {
            "messages": [
                {"sender_type": " customer ", "body": "trimmed sender"},
            ]
        }
        message = shadow._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "trimmed sender")

        convo = {
            "messages": [
                {"body": "system message"},
                {"sender_type": "customer", "body": "real customer"},
            ]
        }
        message = shadow._extract_latest_customer_message({}, convo)
        self.assertEqual(message, "real customer")

    def test_extract_order_payload(self) -> None:
        ticket = {"order": {"order_id": "o-1"}, "__source_path": "/v1/tickets/1"}
        convo = {"orders": [{"tracking_number": "TN123"}]}
        merged = shadow._extract_order_payload(ticket, convo)
        self.assertEqual(merged.get("order_id"), "o-1")
        self.assertEqual(merged.get("tracking_number"), "TN123")
        self.assertNotIn("__source_path", merged)

    def test_lookup_order_summary_payload_first_shopify(self) -> None:
        class _ShopifyClient:
            def get_order(self, *args, **kwargs):
                payload = {
                    "order": {
                        "created_at": "2024-01-01T00:00:00Z",
                        "fulfillments": [
                            {"tracking_number": "TN123", "tracking_company": "UPS"}
                        ],
                        "shipping_lines": [{"title": "Standard"}],
                    }
                }
                return _StubShopifyResponse(payload)

        envelope = shadow._build_event_envelope(
            {"order_id": "o-1"}, ticket_id="t-1"
        )
        summary, source = shadow._lookup_order_summary_payload_first(
            envelope, allow_network=True, shopify_client=_ShopifyClient()
        )
        self.assertEqual(source, "shopify")
        self.assertEqual(summary.get("carrier"), "UPS")

    def test_lookup_order_summary_payload_first_payload(self) -> None:
        envelope = shadow._build_event_envelope(
            {"order": {"tracking_number": "TN999"}}, ticket_id="t-9"
        )
        summary, source = shadow._lookup_order_summary_payload_first(
            envelope, allow_network=False, shopify_client=_GuardedShopifyClient()
        )
        self.assertEqual(source, "payload")
        self.assertEqual(summary.get("tracking_number"), "TN999")

    def test_lookup_order_summary_baseline(self) -> None:
        envelope = shadow._build_event_envelope({}, ticket_id="t-1")
        summary, source = shadow._lookup_order_summary_payload_first(
            envelope, allow_network=False, shopify_client=_GuardedShopifyClient()
        )
        self.assertEqual(source, "baseline")
        self.assertIn("order_id", summary)

    def test_lookup_order_summary_skips_missing_order_id(self) -> None:
        envelope = shadow._build_event_envelope({}, ticket_id="t-2")
        summary, source = shadow._lookup_order_summary_payload_first(
            envelope, allow_network=True, shopify_client=_GuardedShopifyClient()
        )
        self.assertEqual(source, "skipped_missing_order_id")
        self.assertEqual(summary.get("order_id"), "unknown")

    def test_fetch_ticket_fallbacks(self) -> None:
        class _SequenceClient:
            def __init__(self):
                self.calls = []

            def request(self, method: str, path: str, **kwargs):
                self.calls.append(path)
                if path.endswith("/v1/tickets/123"):
                    return _StubResponse({}, status_code=404)
                if path.endswith("/v1/tickets/number/123"):
                    return _StubResponse({"ticket": {"id": "t-123"}})
                return _StubResponse({}, status_code=404)

        ticket = shadow._fetch_ticket(_SequenceClient(), "123")
        self.assertEqual(ticket.get("id"), "t-123")

    def test_fetch_ticket_raises(self) -> None:
        class _FailClient:
            def request(self, method: str, path: str, **kwargs):
                raise shadow.RichpanelRequestError("boom")

        with self.assertRaises(RuntimeError):
            shadow._fetch_ticket(_FailClient(), "ticket-xyz")

    def test_fetch_conversation_handles_error(self) -> None:
        class _ErrorClient:
            def request(self, method: str, path: str, **kwargs):
                return _StubResponse({}, status_code=500)

        result = shadow._fetch_conversation(_ErrorClient(), "t-1")
        self.assertEqual(result, {})

    def test_fetch_conversation_handles_exception(self) -> None:
        class _BoomClient:
            def request(self, method: str, path: str, **kwargs):
                raise RuntimeError("boom")

        result = shadow._fetch_conversation(_BoomClient(), "t-1")
        self.assertEqual(result, {})

    def test_main_uses_sample_size_when_no_ticket_id(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        results = [
            {
                "ticket_id_redacted": "redacted:111",
                "routing": {"intent": "order_status_tracking"},
                "customer_presence": {"email_present": True},
                "order_status": {
                    "is_order_status": True,
                    "order_summary_found": True,
                    "tracking_present": True,
                    "eta_window": {"bucket": "on_time"},
                },
            },
            {
                "ticket_id_redacted": "redacted:222",
                "routing": {"intent": "refund_request"},
                "customer_presence": {"email_present": False},
                "order_status": {
                    "is_order_status": False,
                    "order_summary_found": False,
                    "tracking_present": False,
                    "eta_window": None,
                },
            },
        ]
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            out_path = Path(tmpdir) / "out.json"
            trace_path = Path(tmpdir) / "trace.json"
            argv = [
                "shadow_order_status.py",
                "--sample-size",
                "2",
                "--out",
                str(out_path),
                "--max-tickets",
                "5",
                "--confirm-live-readonly",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow, "_fetch_recent_ticket_refs", return_value=["t-1", "t-2"]
            ), mock.patch.object(
                shadow, "run_ticket", side_effect=results
            ), mock.patch.object(
                shadow, "_build_shopify_client", return_value=_GuardedShopifyClient()
            ), mock.patch.object(
                shadow, "_build_trace_path", return_value=trace_path
            ):
                result = shadow.main()
            self.assertEqual(result, 0)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["sample_mode"], "recent")
            self.assertEqual(payload["counts"]["tickets_scanned"], 2)
            self.assertEqual(payload["counts"]["orders_matched"], 1)
            self.assertEqual(payload["counts"]["tracking_found"], 1)

    def test_main_sample_size_over_max_tickets_rejected(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            out_path = Path(tmpdir) / "out.json"
            argv = [
                "shadow_order_status.py",
                "--sample-size",
                "3",
                "--out",
                str(out_path),
                "--max-tickets",
                "2",
                "--confirm-live-readonly",
            ]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit):
                    shadow.main()

    def test_main_output_redacts_pii(self) -> None:
        ticket_payload = {
            "id": "t-1",
            "created_at": "2024-01-02T00:00:00Z",
            "customer_message": "where is my order",
            "order": {
                "order_id": "o-1",
                "tracking_number": "TN123456",
                "carrier": "UPS",
                "created_at": "2024-01-01T00:00:00Z",
                "shipping_method": "Standard",
            },
            "customer": {"email": "customer@example.com", "name": "Test User"},
            "shipping_address": {"line1": "123 Main"},
        }
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        routing = SimpleNamespace(
            intent="order_status_tracking",
            department="Email Support Team",
            reason="stubbed",
        )
        routing_artifact = SimpleNamespace(
            primary_source="deterministic",
            llm_suggestion={
                "confidence": 0.42,
                "model": "gpt-test",
                "response_id": "resp-test",
                "gated_reason": "outbound_disabled",
            },
        )
        stub_client = _GuardedRichpanelClient(ticket_payload, {})
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            out_path = Path(tmpdir) / "out.json"
            trace_path = Path(tmpdir) / "trace.json"
            argv = [
                "shadow_order_status.py",
                "--ticket-id",
                "t-1",
                "--out",
                str(out_path),
                "--max-tickets",
                "1",
                "--confirm-live-readonly",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow, "_build_shopify_client", return_value=_GuardedShopifyClient()
            ), mock.patch.object(
                shadow, "_build_trace_path", return_value=trace_path
            ), mock.patch.object(
                shadow, "compute_dual_routing", return_value=(routing, routing_artifact)
            ):
                result = shadow.main()
            self.assertEqual(result, 0)
            raw = out_path.read_text(encoding="utf-8")
            self.assertNotIn("customer@example.com", raw)
            self.assertNotIn("Test User", raw)
            self.assertNotIn("123 Main", raw)
            self.assertNotIn("TN123456", raw)
            payload = json.loads(raw)
            ticket_entry = payload["tickets"][0]
            self.assertTrue(ticket_entry["ticket_id_redacted"].startswith("redacted:"))
            self.assertTrue(ticket_entry["customer_presence"]["name_present"])
            self.assertTrue(ticket_entry["order_status"]["tracking_present"])

    def test_main_error_is_redacted(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            out_path = Path(tmpdir) / "out.json"
            trace_path = Path(tmpdir) / "trace.json"
            argv = [
                "shadow_order_status.py",
                "--ticket-id",
                "t-1",
                "--out",
                str(out_path),
                "--max-tickets",
                "1",
                "--confirm-live-readonly",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow, "run_ticket", side_effect=RuntimeError("email=x@y.com")
            ), mock.patch.object(
                shadow, "_build_shopify_client", return_value=_GuardedShopifyClient()
            ), mock.patch.object(
                shadow, "_build_trace_path", return_value=trace_path
            ):
                result = shadow.main()
            self.assertEqual(result, 1)
            raw = out_path.read_text(encoding="utf-8")
            self.assertNotIn("x@y.com", raw)
            payload = json.loads(raw)
            err = payload["tickets"][0]["error"]
            self.assertEqual(err["type"], "error")

    def test_main_continues_after_failure(self) -> None:
        env = {
            "RICHPANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        success_result = {
            "ticket_id_redacted": "redacted:abc123",
            "routing": {"intent": "unknown", "confidence": 0.0},
            "customer_presence": {"email_present": True, "name_present": True},
            "order_status": {"is_order_status": False},
        }
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            out_path = Path(tmpdir) / "out.json"
            trace_path = Path(tmpdir) / "trace.json"
            argv = [
                "shadow_order_status.py",
                "--ticket-id",
                "t-1",
                "--ticket-id",
                "t-2",
                "--out",
                str(out_path),
                "--max-tickets",
                "2",
                "--confirm-live-readonly",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow, "run_ticket", side_effect=[RuntimeError("boom"), success_result]
            ), mock.patch.object(
                shadow, "_build_shopify_client", return_value=_GuardedShopifyClient()
            ), mock.patch.object(
                shadow, "_build_trace_path", return_value=trace_path
            ):
                result = shadow.main()
            self.assertEqual(result, 1)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["tickets"]), 2)
            self.assertEqual(payload["tickets"][0]["error"]["type"], "error")
            self.assertTrue(
                payload["tickets"][1]["ticket_id_redacted"].startswith("redacted:")
            )


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ShadowOrderStatusGuardTests)
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            ShadowOrderStatusHelperTests
        )
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            ShadowOrderStatusRedactionTests
        )
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(ShadowOrderStatusTraceTests)
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            ShadowOrderStatusNoWriteTests
        )
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
