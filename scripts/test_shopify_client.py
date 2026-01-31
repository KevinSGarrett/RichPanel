from __future__ import annotations

import json
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
    ShopifyWriteDisabledError,
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
        self.put_calls = []

    def get_secret_value(self, SecretId):
        self.calls.append(SecretId)
        response = self.responses.get(SecretId, {})
        if isinstance(response, Exception):
            raise response
        return response

    def put_secret_value(self, SecretId, SecretString):
        self.put_calls.append(SecretId)
        self.responses[SecretId] = {"SecretString": SecretString}


class ShopifyClientTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure defaults do not inherit host environment flags.
        for key in [
            "SHOPIFY_OUTBOUND_ENABLED",
            "SHOPIFY_ACCESS_TOKEN_OVERRIDE",
            "SHOPIFY_SHOP_DOMAIN",
            "SHOPIFY_SHOP",
            "SHOPIFY_API_VERSION",
            "RICHPANEL_ENV",
            "RICH_PANEL_ENV",
            "MW_ENV",
            "ENV",
            "ENVIRONMENT",
            "MW_PROD_WRITES_ACK",
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
        self.assertEqual(headers["X-Shopify-Access-Token"], "secret")
        self.assertEqual(headers["Authorization"], "Bearer abc")

    def test_prod_write_requires_ack(self) -> None:
        os.environ["MW_ENV"] = "prod"
        transport = _FailingTransport()
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        with self.assertRaises(ShopifyWriteDisabledError):
            client.request(
                "POST",
                "/admin/api/2024-01/orders.json",
                safe_mode=False,
                automation_enabled=True,
                dry_run=False,
            )

        self.assertFalse(transport.called)

    def test_safe_mode_short_circuits_before_prod_ack(self) -> None:
        os.environ["MW_ENV"] = "prod"
        transport = _FailingTransport()
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        response = client.request(
            "POST",
            "/admin/api/2024-01/orders.json",
            safe_mode=True,
            automation_enabled=True,
            dry_run=False,
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "safe_mode")
        self.assertFalse(transport.called)

    def test_prod_write_ack_allows_network(self) -> None:
        os.environ["MW_ENV"] = "prod"
        os.environ["MW_PROD_WRITES_ACK"] = "true"
        transport = _RecordingTransport(
            [TransportResponse(status_code=201, headers={}, body=b'{"ok": true}')]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        response = client.request(
            "POST",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
            dry_run=False,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(transport.requests), 1)

    def test_non_prod_write_unaffected_by_prod_ack(self) -> None:
        os.environ["MW_ENV"] = "dev"
        transport = _RecordingTransport(
            [TransportResponse(status_code=201, headers={}, body=b'{"ok": true}')]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        response = client.request(
            "POST",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
            dry_run=False,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(transport.requests), 1)

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

    def test_token_diagnostics_for_override(self) -> None:
        client = ShopifyClient(access_token="shpat_override")
        diagnostics = client.token_diagnostics()
        self.assertEqual(diagnostics.get("token_type"), "offline")
        self.assertEqual(diagnostics.get("raw_format"), "override")

    def test_json_secret_parses_refresh_token(self) -> None:
        secret_id = "rp-mw/local/shopify/admin_api_token"
        secrets = _StubSecretsClient(
            {
                "SecretString": json.dumps(
                    {"access_token": "shpua-token", "refresh_token": "refresh"}
                )
            }
        )
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b"{}")]
        )
        client = ShopifyClient(
            allow_network=True,
            transport=transport,
            secrets_client=secrets,
            access_token_secret_id=secret_id,
        )

        response = client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(transport.requests[0].headers["x-shopify-access-token"], "shpua-token")
        diagnostics = client.token_diagnostics()
        self.assertEqual(diagnostics.get("token_type"), "online")
        self.assertTrue(diagnostics.get("has_refresh_token"))

    def test_token_diagnostics_detects_prefixes(self) -> None:
        client = ShopifyClient(access_token="shpat_offline")
        self.assertEqual(client.token_diagnostics().get("token_type"), "offline")
        client = ShopifyClient(access_token="shpua_online")
        self.assertEqual(client.token_diagnostics().get("token_type"), "online")

    def test_parse_expires_at_and_expires_in(self) -> None:
        client = ShopifyClient(access_token="test-token")
        expires_at = client._parse_expires_at({"expires_at": "2026-01-30T00:00:00Z"})
        self.assertIsNotNone(expires_at)
        expires_in = client._parse_expires_at({"expires_in": 3600, "issued_at": 1000})
        self.assertEqual(expires_in, 4600)

    def test_refresh_access_token_returns_false_without_refresh_token(self) -> None:
        client = ShopifyClient(access_token="shpat_token")
        self.assertFalse(client.refresh_access_token())

    def test_parse_expires_at_iso_timestamp(self) -> None:
        secret_id = "rp-mw/local/shopify/admin_api_token"
        secrets = _StubSecretsClient(
            {
                "SecretString": json.dumps(
                    {
                        "access_token": "shpua-token",
                        "refresh_token": "refresh",
                        "expires_at": "3026-01-30T00:00:00Z",
                    }
                )
            }
        )
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b"{}")]
        )
        client = ShopifyClient(
            allow_network=True,
            transport=transport,
            secrets_client=secrets,
            access_token_secret_id=secret_id,
        )
        client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )
        diagnostics = client.token_diagnostics()
        self.assertIsNotNone(diagnostics.get("expires_at"))

    def test_refresh_access_token_updates_secret(self) -> None:
        token_secret = "rp-mw/local/shopify/admin_api_token"
        client_id_secret = "rp-mw/local/shopify/client_id"
        client_secret_secret = "rp-mw/local/shopify/client_secret"
        secrets = _SelectiveStubSecretsClient(
            {
                token_secret: {
                    "SecretString": json.dumps(
                        {"access_token": "old-token", "refresh_token": "refresh"}
                    )
                },
                client_id_secret: {"SecretString": "client-id"},
                client_secret_secret: {"SecretString": "client-secret"},
            }
        )
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=b'{"access_token":"new-token","refresh_token":"new-refresh","expires_in":3600}',
                )
            ]
        )
        with mock.patch.dict(
            os.environ,
            {
                "SHOPIFY_CLIENT_ID_SECRET_ID": client_id_secret,
                "SHOPIFY_CLIENT_SECRET_SECRET_ID": client_secret_secret,
            },
            clear=False,
        ):
            client = ShopifyClient(
                allow_network=True,
                transport=transport,
                secrets_client=secrets,
                access_token_secret_id=token_secret,
            )
            refreshed = client.refresh_access_token()

        self.assertTrue(refreshed)
        self.assertIn(token_secret, secrets.put_calls)

    def test_refresh_access_token_handles_bad_response(self) -> None:
        token_secret = "rp-mw/local/shopify/admin_api_token"
        client_id_secret = "rp-mw/local/shopify/client_id"
        client_secret_secret = "rp-mw/local/shopify/client_secret"
        secrets = _SelectiveStubSecretsClient(
            {
                token_secret: {
                    "SecretString": json.dumps(
                        {"access_token": "old-token", "refresh_token": "refresh"}
                    )
                },
                client_id_secret: {"SecretString": "client-id"},
                client_secret_secret: {"SecretString": "client-secret"},
            }
        )
        transport = _RecordingTransport(
            [TransportResponse(status_code=500, headers={}, body=b"")]
        )
        with mock.patch.dict(
            os.environ,
            {
                "SHOPIFY_CLIENT_ID_SECRET_ID": client_id_secret,
                "SHOPIFY_CLIENT_SECRET_SECRET_ID": client_secret_secret,
            },
            clear=False,
        ):
            client = ShopifyClient(
                allow_network=True,
                transport=transport,
                secrets_client=secrets,
                access_token_secret_id=token_secret,
            )
            refreshed = client.refresh_access_token()

        self.assertFalse(refreshed)

    def test_expires_in_sets_expiry(self) -> None:
        client = ShopifyClient(access_token="shpua-token")
        expires_at = client._parse_expires_at(
            {"expires_in": 60, "issued_at": 1000}
        )
        self.assertEqual(expires_at, 1060.0)

    def test_refresh_on_401_retries_once(self) -> None:
        token_secret_id = "rp-mw/local/shopify/admin_api_token"
        client_id_secret_id = "rp-mw/local/shopify/client_id"
        client_secret_secret_id = "rp-mw/local/shopify/client_secret"
        secrets = _SelectiveStubSecretsClient(
            {
                token_secret_id: {
                    "SecretString": json.dumps(
                        {"access_token": "expired", "refresh_token": "refresh-token"}
                    )
                },
                client_id_secret_id: {"SecretString": "client-id"},
                client_secret_secret_id: {"SecretString": "client-secret"},
            }
        )
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=401, headers={}, body=b""),
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=b'{"access_token":"new-token","refresh_token":"new-refresh","expires_in":3600}',
                ),
                TransportResponse(status_code=200, headers={}, body=b"{}"),
            ]
        )
        with mock.patch.dict(
            os.environ,
            {
                "SHOPIFY_CLIENT_ID_SECRET_ID": client_id_secret_id,
                "SHOPIFY_CLIENT_SECRET_SECRET_ID": client_secret_secret_id,
            },
            clear=False,
        ):
            client = ShopifyClient(
                allow_network=True,
                transport=transport,
                secrets_client=secrets,
                access_token_secret_id=token_secret_id,
            )

            response = client.request(
                "GET",
                "/admin/api/2024-01/orders.json",
                safe_mode=False,
                automation_enabled=True,
            )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 3)
        self.assertEqual(
            transport.requests[1].url,
            "https://example.myshopify.com/admin/oauth/access_token",
        )
        self.assertIn(token_secret_id, secrets.put_calls)

    def test_refresh_skips_without_refresh_token(self) -> None:
        token_secret_id = "rp-mw/local/shopify/admin_api_token"
        secrets = _StubSecretsClient(
            {"SecretString": json.dumps({"access_token": "expired"})}
        )
        transport = _RecordingTransport(
            [TransportResponse(status_code=401, headers={}, body=b"")]
        )
        client = ShopifyClient(
            allow_network=True,
            transport=transport,
            secrets_client=secrets,
            access_token_secret_id=token_secret_id,
        )

        response = client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertEqual(response.status_code, 401)

    def test_refresh_fails_without_client_credentials(self) -> None:
        token_secret_id = "rp-mw/local/shopify/admin_api_token"
        secrets = _StubSecretsClient(
            {
                "SecretString": json.dumps(
                    {"access_token": "expired", "refresh_token": "refresh"}
                )
            }
        )
        transport = _RecordingTransport(
            [TransportResponse(status_code=401, headers={}, body=b"")]
        )
        client = ShopifyClient(
            allow_network=True,
            transport=transport,
            secrets_client=secrets,
            access_token_secret_id=token_secret_id,
        )

        response = client.request(
            "GET",
            "/admin/api/2024-01/orders.json",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertEqual(response.status_code, 401)

    def test_parse_timestamp_invalid(self) -> None:
        client = ShopifyClient(access_token="test-token")
        self.assertIsNone(client._parse_timestamp("not-a-date"))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ShopifyClientTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
