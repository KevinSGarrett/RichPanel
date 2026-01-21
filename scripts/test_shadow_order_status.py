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


class ShadowOrderStatusGuardTests(unittest.TestCase):
    def test_requires_readonly_flags(self) -> None:
        env = {
            "RICHANEL_ENV": "staging",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("RICHPANEL_READ_ONLY", str(ctx.exception))

    def test_requires_confirm_flag(self) -> None:
        env = {
            "RICHANEL_ENV": "staging",
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
            "RICHANEL_ENV": "dev",
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
            "RICHANEL_ENV": "staging",
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("MW_ALLOW_NETWORK_READS", str(ctx.exception))

    def test_requires_richanel_env(self) -> None:
        env = {
            "RICHPANEL_READ_ONLY": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
            "MW_ALLOW_NETWORK_READS": "true",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow._require_readonly_guards(confirm_live_readonly=True)
        self.assertIn("RICHANEL_ENV", str(ctx.exception))

    def test_shopify_secret_override_guard(self) -> None:
        env = {"SHOPIFY_ACCESS_TOKEN_OVERRIDE": "tok"}
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
            "RICHANEL_ENV": "staging",
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
