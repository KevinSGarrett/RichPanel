from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelClient,
    RichpanelExecutor,
    RichpanelRequestError,
    RichpanelWriteDisabledError,
    TransportError,
    TransportRequest,
    TransportResponse,
)
from integrations.common import PROD_WRITE_ACK_PHRASE, prod_write_ack_matches  # noqa: E402


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


class RichpanelClientTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure defaults do not inherit host environment flags.
        os.environ.pop("RICHPANEL_OUTBOUND_ENABLED", None)
        os.environ.pop("RICHPANEL_API_KEY_OVERRIDE", None)
        os.environ.pop("RICHPANEL_ENV", None)
        os.environ.pop("RICH_PANEL_ENV", None)
        os.environ.pop("RICHPANEL_WRITE_DISABLED", None)
        os.environ.pop("MW_ENV", None)
        os.environ.pop("ENV", None)
        os.environ.pop("ENVIRONMENT", None)
        os.environ.pop("MW_PROD_WRITES_ACK", None)

    def test_dry_run_default_skips_transport(self) -> None:
        transport = _FailingTransport()
        client = RichpanelClient(api_key="test-key", transport=transport)

        response = client.request("GET", "/v1/tickets/example")

        self.assertTrue(response.dry_run)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(transport.called)

    def test_env_namespace_is_reflected_in_secret_path(self) -> None:
        os.environ["RICH_PANEL_ENV"] = "Staging"

        client = RichpanelClient(api_key="test-key")

        self.assertEqual(client.environment, "staging")
        self.assertEqual(client.api_key_secret_id, "rp-mw/staging/richpanel/api_key")

    def test_env_flag_allows_outbound_requests(self) -> None:
        os.environ["RICHPANEL_OUTBOUND_ENABLED"] = "true"
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=200, headers={}, body=b'{"ok": true}'),
            ]
        )
        client = RichpanelClient(api_key="test-key", transport=transport)

        response = client.request("GET", "/v1/ping")

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 1)

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
        client = RichpanelClient(
            api_key="test-key",
            dry_run=False,
            transport=transport,
            sleeper=lambda seconds: sleeps.append(seconds),
            rng=lambda: 0.0,
        )

        response = client.request("GET", "/v1/tickets/abc")

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 2)
        self.assertGreaterEqual(sleeps[0], 1.0)
        self.assertIn(len(sleeps), (1, 2))
        if len(sleeps) == 2:
            self.assertGreaterEqual(sleeps[1], 0.0)

    def test_transport_errors_retry_and_raise(self) -> None:
        class _ErrorTransport:
            def __init__(self):
                self.calls = 0

            def send(self, request: TransportRequest) -> TransportResponse:
                self.calls += 1
                raise TransportError("boom")

        sleeps = []
        transport = _ErrorTransport()
        client = RichpanelClient(
            api_key="test-key",
            dry_run=False,
            transport=transport,
            sleeper=lambda seconds: sleeps.append(seconds),
            rng=lambda: 0.0,
            max_attempts=2,
        )

        with self.assertRaises(RichpanelRequestError):
            client.request("GET", "/v1/tags")

        self.assertEqual(transport.calls, 2)
        self.assertEqual(len(sleeps), 1)
        self.assertGreaterEqual(sleeps[0], client.backoff_seconds)

    def test_redaction_masks_api_key(self) -> None:
        redacted = RichpanelClient.redact_headers(
            {"x-richpanel-key": "secret", "ok": "1"}
        )

        self.assertEqual(redacted["x-richpanel-key"], "***")
        self.assertEqual(redacted["ok"], "1")

    def test_executor_defaults_to_dry_run(self) -> None:
        transport = _FailingTransport()
        executor = RichpanelExecutor(
            client=RichpanelClient(api_key="test-key", transport=transport)
        )

        response = executor.execute("POST", "/v1/tickets/abc", json_body={"foo": "bar"})

        self.assertTrue(response.dry_run)
        self.assertFalse(transport.called)

    def test_executor_respects_outbound_enabled_flag(self) -> None:
        transport = _RecordingTransport(
            [TransportResponse(status_code=202, headers={}, body=b"accepted")]
        )
        executor = RichpanelExecutor(
            client=RichpanelClient(
                api_key="test-key", transport=transport, dry_run=True
            ),
            outbound_enabled=True,
        )

        response = executor.execute(
            "PUT", "/v1/tickets/abc/add-tags", json_body={"tags": ["vip"]}
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(transport.requests), 1)

    def test_writes_blocked_when_write_disabled_env_set(self) -> None:
        os.environ["RICHPANEL_WRITE_DISABLED"] = "true"
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b'{"ok": true}')]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        response = client.request("GET", "/v1/ping", dry_run=False)

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 1)

        for method in ("PUT", "POST", "PATCH", "DELETE"):
            with self.assertRaises(RichpanelWriteDisabledError):
                client.request(method, "/v1/blocked", json_body={"x": 1}, dry_run=False)

        # Transport should only have been called for the GET.
        self.assertEqual(len(transport.requests), 1)

    def test_read_only_blocks_non_get(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=200, headers={}, body=b""),
                TransportResponse(status_code=200, headers={}, body=b""),
            ]
        )
        client = RichpanelClient(
            api_key="test-key", transport=transport, dry_run=False, read_only=True
        )

        response = client.request("GET", "/v1/ping", dry_run=False)
        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)

        response = client.request("HEAD", "/v1/ping", dry_run=False)
        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)

        with self.assertRaises(RichpanelWriteDisabledError):
            client.request("POST", "/v1/blocked", json_body={"x": 1}, dry_run=False)

        # Transport should only be called for GET/HEAD.
        self.assertEqual(len(transport.requests), 2)

    def test_prod_write_requires_ack_even_when_write_enabled(self) -> None:
        os.environ["MW_ENV"] = "prod"
        os.environ["RICHPANEL_READ_ONLY"] = "0"
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b'{"ok": true}')]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        with self.assertRaises(RichpanelWriteDisabledError):
            client.request("POST", "/v1/blocked", json_body={"x": 1}, dry_run=False)

        self.assertEqual(len(transport.requests), 0)

    def test_prod_write_ack_allows_write_when_controls_allow(self) -> None:
        os.environ["MW_ENV"] = "prod"
        os.environ["RICHPANEL_READ_ONLY"] = "0"
        os.environ["MW_PROD_WRITES_ACK"] = "I_UNDERSTAND_PROD_WRITES"
        transport = _RecordingTransport(
            [TransportResponse(status_code=202, headers={}, body=b"accepted")]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        response = client.request(
            "POST", "/v1/tickets", json_body={"ticket_id": "t-1"}, dry_run=False
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(transport.requests), 1)

    def test_prod_write_ack_does_not_bypass_write_disabled(self) -> None:
        os.environ["MW_ENV"] = "prod"
        os.environ["RICHPANEL_READ_ONLY"] = "0"
        os.environ["RICHPANEL_WRITE_DISABLED"] = "1"
        os.environ["MW_PROD_WRITES_ACK"] = "true"
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b'{"ok": true}')]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        with self.assertRaises(RichpanelWriteDisabledError):
            client.request("PATCH", "/v1/blocked", json_body={"x": 1}, dry_run=False)

        self.assertEqual(len(transport.requests), 0)

    def test_non_prod_write_unaffected_by_prod_ack(self) -> None:
        os.environ["MW_ENV"] = "dev"
        os.environ["RICHPANEL_READ_ONLY"] = "0"
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b'{"ok": true}')]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        response = client.request(
            "POST", "/v1/tickets", json_body={"ticket_id": "t-2"}, dry_run=False
        )

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 1)

    def test_get_ticket_metadata_handles_ticket_dict(self) -> None:
        body = (
            b'{"ticket": {"status": "OPEN", "tags": ["vip"], "conversation_no": 123}}'
        )
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=body)]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        meta = client.get_ticket_metadata("abc")

        self.assertEqual(meta.status, "OPEN")
        self.assertEqual(meta.tags, ["vip"])
        self.assertEqual(meta.conversation_no, 123)

    def test_get_ticket_metadata_handles_non_dict_ticket_string(self) -> None:
        body = b'{"ticket": "error", "status": "OPEN", "tags": ["t1"]}'
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=body)]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        meta = client.get_ticket_metadata("abc")

        self.assertEqual(meta.status, "OPEN")
        self.assertEqual(meta.tags, ["t1"])
        self.assertIsNone(meta.conversation_no)

    def test_get_ticket_metadata_handles_non_dict_ticket_number(self) -> None:
        body = b'{"ticket": 123, "status": "CLOSED", "tags": ["t2"]}'
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=body)]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)

        meta = client.get_ticket_metadata("abc")

        self.assertEqual(meta.status, "CLOSED")
        self.assertEqual(meta.tags, ["t2"])
        self.assertIsNone(meta.conversation_no)


class ProdWriteAckTests(unittest.TestCase):
    def test_prod_write_ack_matches_exact_phrase(self) -> None:
        self.assertTrue(prod_write_ack_matches(PROD_WRITE_ACK_PHRASE))

    def test_prod_write_ack_matches_rejects_other_values(self) -> None:
        self.assertFalse(prod_write_ack_matches("true"))
        self.assertFalse(prod_write_ack_matches("I_UNDERSTAND_PROD_WRITES "))


def main() -> int:  # pragma: no cover
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RichpanelClientTests)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ProdWriteAckTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
