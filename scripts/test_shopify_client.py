from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.integrations.shopify import (  # noqa: E402
    ShopifyClient,
    TransportRequest,
    TransportResponse,
)


class _RecordingTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def send(self, request: TransportRequest) -> TransportResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("no response stub provided")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FailingTransport:
    def __init__(self):
        self.called = False

    def send(self, request: TransportRequest) -> TransportResponse:
        self.called = True
        raise AssertionError("transport should not be used in dry-run")


class _StubSecretsClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def get_secret_value(self, SecretId):
        self.calls += 1
        return self.response


class _SelectiveStubSecretsClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get_secret_value(self, SecretId):
        self.calls.append(SecretId)
        response = self.responses.get(SecretId, {})
        if isinstance(response, Exception):
            raise response
        return response


class ShopifyClientTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure defaults do not inherit host environment flags.
        for key in [
            "SHOPIFY_OUTBOUND_ENABLED",
            "SHOPIFY_ACCESS_TOKEN_OVERRIDE",
            "RICHPANEL_ENV",
            "RICH_PANEL_ENV",
            "MW_ENV",
            "ENVIRONMENT",
        ]:
            os.environ.pop(key, None)

    def test_dry_run_default_skips_transport(self) -> None:
        transport = _FailingTransport()
        client = ShopifyClient(access_token="test-token", transport=transport)

        response = client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_disabled")
        self.assertEqual(response.headers.get("x-dry-run"), "1")
        self.assertFalse(transport.called)

    def test_get_order_builds_expected_path_and_query(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=200, headers={}, body=b"{}"),
            ]
        )
        client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )

        response = client.get_order(
            "order 123",
            fields=["name", "id"],
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url,
            "https://example.myshopify.com/admin/api/2024-01/orders/order%20123.json?fields=id%2Cname",
        )

    def test_find_order_by_name_builds_expected_query(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=200, headers={}, body=b"{}"),
            ]
        )
        client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )

        response = client.find_order_by_name(
            "#1158259",
            fields=["id", "name"],
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url,
            "https://example.myshopify.com/admin/api/2024-01/orders.json?fields=id%2Cname&limit=5&name=%231158259&status=any",
        )

    def test_get_order_respects_network_blocked_gate(self) -> None:
        transport = _FailingTransport()
        client = ShopifyClient(
            access_token="test-token",
            transport=transport,
        )

        response = client.get_order("123")

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_disabled")
        self.assertFalse(transport.called)

    def test_retries_on_429_and_honors_retry_after(self) -> None:
        sleeps = []
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=429, headers={"Retry-After": "1"}, body=b""
                ),
                TransportResponse(status_code=200, headers={}, body=b'{"ok": true}'),
            ]
        )
        client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
            sleeper=lambda seconds: sleeps.append(seconds),
            rng=lambda: 0.0,
        )

        response = client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(sleeps, [1.0])

    def test_redaction_masks_tokens(self) -> None:
        headers = {
            "X-Shopify-Access-Token": "secret",
            "Authorization": "Bearer abc",
            "ok": "1",
        }
        redacted = ShopifyClient.redact_headers(headers)

        self.assertEqual(redacted["X-Shopify-Access-Token"], "***")
        self.assertEqual(redacted["Authorization"], "***")
        self.assertEqual(redacted["ok"], "1")
        self.assertEqual(
            headers["X-Shopify-Access-Token"], "secret"
        )  # original untouched

    def test_env_namespace_is_reflected_in_secret_path(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "RICHPANEL_ENV": "Staging",
                "RICH_PANEL_ENV": "Staging",
                "MW_ENV": "Staging",
                "ENVIRONMENT": "Staging",
            },
            clear=True,
        ):
            client = ShopifyClient(access_token="test-token")

            self.assertEqual(client.environment, "staging")
            self.assertEqual(
                client.access_token_secret_id, "rp-mw/staging/shopify/admin_api_token"
            )
            self.assertIn(
                "rp-mw/staging/shopify/access_token", client._secret_id_candidates
            )

    def test_falls_back_to_legacy_secret_when_canonical_missing(self) -> None:
        canonical = "rp-mw/local/shopify/admin_api_token"
        legacy = "rp-mw/local/shopify/access_token"
        secrets = _SelectiveStubSecretsClient(
            {
                canonical: {},
                legacy: {"SecretString": "legacy-token"},
            }
        )
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=200, headers={}, body=b"{}"),
            ]
        )

        with mock.patch.dict(
            os.environ,
            {
                "RICHPANEL_ENV": "local",
                "RICH_PANEL_ENV": "local",
                "MW_ENV": "local",
                "ENVIRONMENT": "local",
            },
            clear=True,
        ):
            client = ShopifyClient(
                allow_network=True,
                transport=transport,
                secrets_client=secrets,
            )

            response = client.request(
                "GET",
                "/admin/api/2024-01/orders.json",
                safe_mode=False,
                automation_enabled=True,
            )

            self.assertFalse(response.dry_run)
            self.assertEqual(client.access_token_secret_id, legacy)
            self.assertEqual(secrets.calls, [canonical, legacy])
            self.assertEqual(
                transport.requests[0].headers["x-shopify-access-token"], "legacy-token"
            )

    def test_missing_secret_short_circuits(self) -> None:
        transport = _FailingTransport()
        secrets = _StubSecretsClient({})
        client = ShopifyClient(
            allow_network=True,
            transport=transport,
            secrets_client=secrets,
        )

        response = client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertTrue(response.dry_run)
        self.assertIn(
            response.reason,
            {"missing_access_token", "secret_lookup_failed", "boto3_unavailable"},
        )
        self.assertFalse(transport.called)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ShopifyClientTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
