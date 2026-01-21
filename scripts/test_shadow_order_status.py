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


class ShadowOrderStatusGuardTests(unittest.TestCase):
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


class ShadowOrderStatusRedactionTests(unittest.TestCase):
    def test_email_hash_and_last4(self) -> None:
        hashed = shadow._hash_email("User@example.com")
        self.assertTrue(hashed.startswith("hash:"))
        self.assertNotIn("User@example.com", hashed)
        self.assertEqual(shadow._last4("TN123456"), "3456")

    def test_customer_redaction(self) -> None:
        ticket = {"customer": {"email": "a@example.com", "name": "Alice"}}
        convo = {"customer_profile": {"phone": "555-1212", "address": "123 Main"}}
        redacted = shadow._extract_customer_redaction(ticket, convo)
        self.assertTrue(redacted["email"].startswith("hash:"))
        self.assertEqual(redacted["name"], "REDACTED")
        self.assertEqual(redacted["phone"], "REDACTED")
        self.assertEqual(redacted["address"], "REDACTED")

    def test_redact_path_variants(self) -> None:
        self.assertEqual(shadow._redact_path(""), "/")
        redacted = shadow._redact_path("/v1/tickets/91608")
        self.assertIn("/v1/tickets/", redacted)
        self.assertNotIn("91608", redacted)
        redacted = shadow._redact_path("/api/v1/orders/ABC")
        self.assertIn("/ABC", redacted)
        self.assertNotIn("redacted:", redacted)


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
        self.assertEqual(result["order_status"]["tracking_number_last4"], "3456")
        self.assertEqual(result["customer"]["name"], "REDACTED")

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

        with self.assertRaises(SystemExit):
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
            self.assertEqual(ticket_entry["customer"]["name"], "REDACTED")
            self.assertEqual(
                ticket_entry["order_status"]["tracking_number_last4"], "3456"
            )


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ShadowOrderStatusGuardTests)
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
