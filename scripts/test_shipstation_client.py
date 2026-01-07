from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.integrations.shipstation import (  # noqa: E402
    ShipStationClient,
    ShipStationExecutor,
    ShipStationResponse,
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
        raise AssertionError("transport should not be used during dry-run")


class _StubSecretsClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def get_secret_value(self, SecretId):
        self.calls += 1
        return self.response


class ShipStationClientTests(unittest.TestCase):
    def setUp(self) -> None:
        for key in [
            "SHIPSTATION_OUTBOUND_ENABLED",
            "SHIPSTATION_API_KEY_OVERRIDE",
            "SHIPSTATION_API_SECRET_OVERRIDE",
            "SHIPSTATION_API_BASE_URL",
            "SHIPSTATION_API_BASE_OVERRIDE",
        ]:
            os.environ.pop(key, None)

    def test_dry_run_default_skips_transport(self) -> None:
        transport = _FailingTransport()
        client = ShipStationClient(api_key="key", api_secret="secret", transport=transport)

        response = client.request(
            "GET",
            "/shipments",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_disabled")
        self.assertEqual(response.headers.get("x-dry-run"), "1")
        self.assertFalse(transport.called)

    def test_list_shipments_builds_expected_path_and_sorted_query(self) -> None:
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b"{}")]
        )
        client = ShipStationClient(
            api_key="key",
            api_secret="secret",
            allow_network=True,
            transport=transport,
        )

        response = client.list_shipments(
            params={"b": "2", "a": "1"},
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 1)
        request = transport.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertTrue(request.url.endswith("/shipments?a=1&b=2"))

    def test_list_shipments_respects_network_blocked_gate(self) -> None:
        transport = _FailingTransport()
        client = ShipStationClient(
            api_key="key",
            api_secret="secret",
            allow_network=False,
            transport=transport,
        )

        response = client.list_shipments(
            params={"page": "1"},
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_disabled")
        self.assertFalse(transport.called)

    def test_missing_credentials_short_circuits(self) -> None:
        transport = _FailingTransport()
        secrets_client = _StubSecretsClient({})
        client = ShipStationClient(
            allow_network=True,
            transport=transport,
            secrets_client=secrets_client,
        )

        response = client.request(
            "POST",
            "/orders/createorder",
            json_body={"orderNumber": "A-123"},
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "missing_credentials")
        self.assertFalse(transport.called)

    def test_retry_honors_retry_after_header(self) -> None:
        sleeps: list[float] = []
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=429, headers={"Retry-After": "2"}, body=b""),
                TransportResponse(status_code=200, headers={}, body=b'{"ok": true}'),
            ]
        )
        client = ShipStationClient(
            api_key="key",
            api_secret="secret",
            allow_network=True,
            transport=transport,
            sleeper=lambda seconds: sleeps.append(seconds),
            rng=lambda: 0.0,
        )

        response = client.request(
            "GET",
            "/fulfillments",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(sleeps, [2.0])

    def test_redaction_masks_sensitive_headers(self) -> None:
        headers = {
            "Authorization": "Basic secret",
            "authorization": "Basic secret-two",
            "X-ShipStation-Key": "abc",
            "X-Other": "ok",
        }

        redacted = ShipStationClient.redact_headers(headers)

        self.assertEqual(redacted["Authorization"], "***")
        self.assertEqual(redacted["authorization"], "***")
        self.assertEqual(redacted["X-ShipStation-Key"], "***")
        self.assertEqual(redacted["X-Other"], "ok")
        self.assertEqual(headers["Authorization"], "Basic secret")

    def test_executor_blocks_without_env_flag(self) -> None:
        transport = _FailingTransport()
        client = ShipStationClient(
            api_key="key",
            api_secret="secret",
            allow_network=True,
            transport=transport,
        )
        executor = ShipStationExecutor(client=client, outbound_enabled=False)

        response = executor.execute(
            "DELETE",
            "/customers/123",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_disabled")
        self.assertFalse(transport.called)

    def test_executor_allows_outbound_when_enabled(self) -> None:
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b"{}")]
        )
        client = ShipStationClient(
            api_key="key",
            api_secret="secret",
            allow_network=True,
            transport=transport,
        )
        executor = ShipStationExecutor(client=client, outbound_enabled=True)

        response = executor.execute(
            "GET",
            "/accounts",
            safe_mode=False,
            automation_enabled=True,
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 1)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ShipStationClientTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())


