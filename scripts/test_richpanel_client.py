from __future__ import annotations

import base64
import os
import sys
import time
import unittest
import urllib.error
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    ClientError,
    RichpanelResponse,
    TicketMetadata,
    RichpanelClient,
    RichpanelExecutor,
    RichpanelRequestError,
    SecretLoadError,
    RichpanelWriteDisabledError,
    HttpTransport,
    TokenBucketRateLimiter,
    get_rate_limiter_stats,
    _redact_url_path,
    _coerce_str,
    _normalize_tag_list,
    _to_bool,
    _truncate,
    _parse_reset_after,
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


class _StubSecretsClient:
    def __init__(self, secrets):
        self.secrets = dict(secrets)
        self.calls = []

    def get_secret_value(self, SecretId):
        self.calls.append(SecretId)
        value = self.secrets.get(SecretId)
        if value is None:
            return {}
        return {"SecretString": value}


class _BinarySecretsClient:
    def __init__(self, payload: bytes):
        self.payload = payload

    def get_secret_value(self, SecretId):
        return {"SecretBinary": self.payload}


class _ErrorSecretsClient:
    def get_secret_value(self, SecretId):
        raise ClientError({"Error": {"Code": "Boom", "Message": "boom"}}, "GetSecretValue")


class RichpanelClientTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure defaults do not inherit host environment flags.
        os.environ.pop("RICHPANEL_OUTBOUND_ENABLED", None)
        os.environ.pop("RICHPANEL_API_KEY_OVERRIDE", None)
        os.environ.pop("RICHPANEL_ENV", None)
        os.environ.pop("RICH_PANEL_ENV", None)
        os.environ.pop("RICHPANEL_WRITE_DISABLED", None)
        os.environ.pop("RICHPANEL_TOKEN_POOL_ENABLED", None)
        os.environ.pop("RICHPANEL_TOKEN_POOL_SECRET_IDS", None)
        os.environ.pop("MW_ENV", None)
        os.environ.pop("ENV", None)
        os.environ.pop("ENVIRONMENT", None)
        os.environ.pop("MW_PROD_WRITES_ACK", None)
        os.environ.pop("RICHPANEL_RATE_LIMIT_RPS", None)
        os.environ.pop("RICHPANEL_429_COOLDOWN_MULTIPLIER", None)
        import richpanel_middleware.integrations.richpanel.client as rp_client

        rp_client._GLOBAL_RATE_LIMITER = None

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

    def test_retries_on_429_honors_reset_header(self) -> None:
        sleeps = []
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=429,
                    headers={"X-RateLimit-Reset": "5"},
                    body=b"",
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
            backoff_max_seconds=1.0,
        )

        response = client.request("GET", "/v1/tickets/abc")

        self.assertFalse(response.dry_run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(transport.requests), 2)
        self.assertGreaterEqual(sleeps[0], 5.0)

    def test_parse_reset_after_epoch_vs_relative(self) -> None:
        with mock.patch(
            "richpanel_middleware.integrations.richpanel.client.time.time",
            return_value=1_700_000_000.0,
        ):
            self.assertEqual(_parse_reset_after("30"), 30.0)
            self.assertAlmostEqual(
                _parse_reset_after("1700000030"), 30.0, places=3
            )
            self.assertIsNone(_parse_reset_after("1699999990"))

    def test_compute_backoff_preserves_retry_after_jitter(self) -> None:
        client = RichpanelClient(
            api_key="test-key",
            dry_run=False,
            backoff_seconds=0.1,
            backoff_max_seconds=1.0,
            rng=lambda: 1.0,
            sleeper=lambda _: None,
        )
        delay = client._compute_backoff(attempt=1, retry_after=10.0)
        self.assertGreaterEqual(delay, 11.0)

    def test_token_pool_rotates_keys(self) -> None:
        os.environ["RICHPANEL_OUTBOUND_ENABLED"] = "true"
        os.environ["RICHPANEL_TOKEN_POOL_ENABLED"] = "true"
        os.environ["RICHPANEL_TOKEN_POOL_SECRET_IDS"] = "id-1,id-2"
        transport = _RecordingTransport(
            [
                TransportResponse(status_code=200, headers={}, body=b'{"ok": true}'),
                TransportResponse(status_code=200, headers={}, body=b'{"ok": true}'),
            ]
        )
        client = RichpanelClient(api_key=None, transport=transport, dry_run=False)
        client._secrets_client_obj = _StubSecretsClient({"id-1": "key-1", "id-2": "key-2"})

        client.request("GET", "/v1/ping", dry_run=False)
        client.request("GET", "/v1/ping", dry_run=False)

        keys = [req.headers.get("x-richpanel-key") for req in transport.requests]
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0], "key-1")
        self.assertEqual(keys[1], "key-2")

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

    def test_sleep_for_cooldown_waits(self) -> None:
        sleeps = []
        client = RichpanelClient(
            api_key="test-key",
            sleeper=lambda seconds: sleeps.append(seconds),
        )
        client._cooldown_until = time.monotonic() + 0.01
        client._sleep_for_cooldown()
        self.assertEqual(len(sleeps), 1)
        self.assertGreater(sleeps[0], 0.0)

    def test_cooldown_multiplier_invalid_defaults(self) -> None:
        os.environ["RICHPANEL_429_COOLDOWN_MULTIPLIER"] = "nope"
        client = RichpanelClient(api_key="test-key")
        self.assertEqual(client._cooldown_multiplier, 1.0)

    def test_register_cooldown_extends_window(self) -> None:
        client = RichpanelClient(api_key="test-key")
        start = time.monotonic()
        client._register_cooldown(0.5)
        self.assertGreaterEqual(client._cooldown_until, start)

    def test_sleep_for_cooldown_no_wait(self) -> None:
        sleeps = []
        client = RichpanelClient(
            api_key="test-key",
            sleeper=lambda seconds: sleeps.append(seconds),
        )
        client._cooldown_until = time.monotonic() - 1.0
        client._sleep_for_cooldown()
        self.assertEqual(sleeps, [])

    def test_register_cooldown_ignores_non_positive(self) -> None:
        client = RichpanelClient(api_key="test-key")
        start = client._cooldown_until
        client._register_cooldown(0.0)
        self.assertEqual(client._cooldown_until, start)

    def test_parse_cooldown_multiplier_default(self) -> None:
        client = RichpanelClient(api_key="test-key")
        self.assertEqual(client._parse_cooldown_multiplier(None), 1.0)

    def test_load_secret_value_binary(self) -> None:
        client = RichpanelClient(api_key="test-key")
        client._secrets_client_obj = _BinarySecretsClient(base64.b64encode(b"key"))
        self.assertEqual(client._load_secret_value("secret"), "key")

    def test_load_token_pool_missing_secret(self) -> None:
        os.environ["RICHPANEL_TOKEN_POOL_ENABLED"] = "true"
        client = RichpanelClient(api_key=None)
        client._token_pool_secret_ids = ["missing"]
        client._secrets_client_obj = _StubSecretsClient({})
        pool = client._load_token_pool()
        self.assertEqual(pool, [])

    def test_rate_limiter_acquire_and_stats(self) -> None:
        clock = {"value": 0.0}
        sleeps = []

        def _clock():
            return clock["value"]

        def _sleep(seconds):
            sleeps.append(seconds)
            clock["value"] += seconds

        limiter = TokenBucketRateLimiter(
            rate=1.0, capacity=1.0, clock=_clock, sleeper=_sleep
        )
        self.assertTrue(limiter.acquire(timeout=1.0))
        self.assertTrue(limiter.acquire(timeout=1.0))
        stats = limiter.get_stats()
        self.assertEqual(stats["total_requests"], 2)
        self.assertGreaterEqual(stats["total_wait_seconds"], 0.0)
        self.assertTrue(sleeps)

    def test_rate_limiter_waits_over_one_second(self) -> None:
        clock = {"value": 0.0}

        def _clock():
            return clock["value"]

        def _sleep(seconds):
            clock["value"] += seconds + 1.1

        limiter = TokenBucketRateLimiter(
            rate=1.0, capacity=1.0, clock=_clock, sleeper=_sleep
        )
        limiter._tokens = 0.0
        self.assertTrue(limiter.acquire(timeout=5.0))
        stats = limiter.get_stats()
        self.assertGreaterEqual(stats["waits_over_1s"], 1)

    def test_rate_limiter_timeout(self) -> None:
        clock = {"value": 0.0}

        def _clock():
            return clock["value"]

        limiter = TokenBucketRateLimiter(
            rate=0.1, capacity=0.0, clock=_clock, sleeper=lambda _: None
        )
        self.assertFalse(limiter.acquire(timeout=0.5))

    def test_rate_limiter_zero_rate(self) -> None:
        limiter = TokenBucketRateLimiter(rate=0.0, capacity=1.0)
        self.assertFalse(limiter.acquire(timeout=0.1))

    def test_global_rate_limiter_disabled(self) -> None:
        os.environ["RICHPANEL_RATE_LIMIT_RPS"] = "0"
        self.assertIsNone(get_rate_limiter_stats())

    def test_global_rate_limiter_enabled(self) -> None:
        os.environ["RICHPANEL_RATE_LIMIT_RPS"] = "1.0"
        import richpanel_middleware.integrations.richpanel.client as rp_client

        rp_client._GLOBAL_RATE_LIMITER = None
        stats = get_rate_limiter_stats()
        self.assertIsNotNone(stats)

    def test_global_rate_limiter_invalid_value(self) -> None:
        os.environ["RICHPANEL_RATE_LIMIT_RPS"] = "nope"
        import richpanel_middleware.integrations.richpanel.client as rp_client

        rp_client._GLOBAL_RATE_LIMITER = None
        self.assertIsNone(get_rate_limiter_stats())

    def test_request_trace_record_and_clear(self) -> None:
        client = RichpanelClient(api_key="test-key")
        client._record_trace(
            method="GET",
            url="https://api.richpanel.com/v1/tickets/123",
            status=200,
            attempt=1,
            retry_after=None,
            retry_delay=None,
        )
        trace = client.get_request_trace()
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["path"], "/v1/tickets/redacted")
        client.clear_request_trace()
        self.assertEqual(client.get_request_trace(), [])

    def test_redact_url_path_handles_bad_url(self) -> None:
        self.assertEqual(_redact_url_path("not a url"), "/redacted")
        self.assertEqual(_redact_url_path(None), "/")  # type: ignore[arg-type]

    def test_http_transport_success(self) -> None:
        transport = HttpTransport()

        class _Resp:
            def __init__(self):
                self.headers = {"x": "1"}

            def read(self):
                return b"{}"

            def getcode(self):
                return 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with mock.patch("urllib.request.urlopen", return_value=_Resp()):
            resp = transport.send(
                TransportRequest(
                    method="GET",
                    url="https://api.richpanel.com/v1/ping",
                    headers={},
                    body=None,
                    timeout=1.0,
                )
            )
        self.assertEqual(resp.status_code, 200)

    def test_http_transport_http_error(self) -> None:
        transport = HttpTransport()
        error = urllib.error.HTTPError(
            url="https://api.richpanel.com/v1/ping",
            code=429,
            msg="Too Many Requests",
            hdrs={"Retry-After": "1"},
            fp=None,
        )

        def _raise(*args, **kwargs):
            raise error

        with mock.patch("urllib.request.urlopen", side_effect=_raise):
            resp = transport.send(
                TransportRequest(
                    method="GET",
                    url="https://api.richpanel.com/v1/ping",
                    headers={},
                    body=None,
                    timeout=1.0,
                )
            )
        self.assertEqual(resp.status_code, 429)

    def test_http_transport_url_error(self) -> None:
        transport = HttpTransport()

        def _raise(*args, **kwargs):
            raise urllib.error.URLError("boom")

        with mock.patch("urllib.request.urlopen", side_effect=_raise):
            with self.assertRaises(TransportError):
                transport.send(
                    TransportRequest(
                        method="GET",
                        url="https://api.richpanel.com/v1/ping",
                        headers={},
                        body=None,
                        timeout=1.0,
                    )
                )

    def test_merge_headers_and_encode_body(self) -> None:
        client = RichpanelClient(api_key="test-key")
        headers = client._merge_headers({"x-richpanel-key": "override"}, "key", True)
        self.assertEqual(headers["x-richpanel-key"], "key")
        self.assertEqual(client._encode_body(b"bytes"), b"bytes")
        self.assertEqual(client._encode_body("text"), b"text")

    def test_build_url_with_params(self) -> None:
        client = RichpanelClient(api_key="test-key", base_url="https://api.richpanel.com")
        url = client._build_url("/v1/tickets", {"status": "open"})
        self.assertIn("status=open", url)

    def test_excerpt_body(self) -> None:
        client = RichpanelClient(api_key="test-key")
        self.assertEqual(client._excerpt_body(b""), "")
        self.assertEqual(client._excerpt_body(b"\xff"), "<binary>")

    def test_resolve_helpers(self) -> None:
        self.assertTrue(_to_bool("true"))
        self.assertEqual(_truncate("longtext", limit=4), "long...")
        self.assertEqual(_coerce_str(" value "), "value")
        self.assertEqual(_normalize_tag_list(["a", "a", None]), ["a"])

    def test_get_ticket_metadata_error_paths(self) -> None:
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b'["list"]')]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)
        with self.assertRaises(RichpanelRequestError):
            client.get_ticket_metadata("123")

    def test_get_ticket_metadata_conversation_no_invalid(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=b'{"ticket":{"status":"open","tags":["vip"],"conversation_no":"x"}}',
                )
            ]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)
        meta = client.get_ticket_metadata("123")
        self.assertEqual(meta.conversation_no, None)

    def test_get_ticket_metadata_dry_run(self) -> None:
        client = RichpanelClient(api_key="test-key", dry_run=True)
        meta = client.get_ticket_metadata("123", dry_run=True)
        self.assertIsInstance(meta, TicketMetadata)
        self.assertEqual(meta.tags, [])

    def test_executor_get_ticket_metadata(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=b'{"ticket":{"status":"open","tags":["vip"]}}',
                )
            ]
        )
        executor = RichpanelExecutor(
            client=RichpanelClient(api_key="test-key", transport=transport, dry_run=False),
            outbound_enabled=True,
        )
        meta = executor.get_ticket_metadata("123")
        self.assertEqual(meta.status, "open")

    def test_rate_limiter_timeout_in_request(self) -> None:
        import richpanel_middleware.integrations.richpanel.client as rp_client

        class _Limiter:
            def acquire(self, timeout=60.0):
                return False

        rp_client._GLOBAL_RATE_LIMITER = _Limiter()
        os.environ["RICHPANEL_RATE_LIMIT_RPS"] = "1"
        client = RichpanelClient(api_key="test-key", dry_run=False)
        with self.assertRaises(RichpanelRequestError):
            client.request("GET", "/v1/ping")
        rp_client._GLOBAL_RATE_LIMITER = None

    def test_trace_enabled_on_transport_error(self) -> None:
        os.environ["RICHPANEL_TRACE_ENABLED"] = "true"

        class _FlakyTransport:
            def __init__(self):
                self.calls = 0

            def send(self, request):
                self.calls += 1
                if self.calls == 1:
                    raise TransportError("boom")
                return TransportResponse(status_code=200, headers={}, body=b"{}")

        client = RichpanelClient(
            api_key="test-key",
            transport=_FlakyTransport(),
            dry_run=False,
            rng=lambda: 0.0,
            sleeper=lambda _: None,
        )
        client.request("GET", "/v1/ping")
        self.assertTrue(client.get_request_trace())

    def test_trace_enabled_on_response(self) -> None:
        os.environ["RICHPANEL_TRACE_ENABLED"] = "true"
        transport = _RecordingTransport(
            [TransportResponse(status_code=200, headers={}, body=b"{}")]
        )
        client = RichpanelClient(api_key="test-key", transport=transport, dry_run=False)
        client.request("GET", "/v1/ping")
        self.assertEqual(client.get_request_trace()[0]["status"], 200)

    def test_cooldown_exception_paths(self) -> None:
        client = RichpanelClient(api_key="test-key")
        client._cooldown_lock = None  # type: ignore[assignment]
        client._sleep_for_cooldown()
        client._register_cooldown(1.0)

    def test_record_trace_timestamp_failure(self) -> None:
        client = RichpanelClient(api_key="test-key")
        with mock.patch("time.time", side_effect=RuntimeError("boom")):
            client._record_trace(
                method="GET",
                url="https://api.richpanel.com/v1/ping",
                status=200,
                attempt=1,
                retry_after=None,
                retry_delay=None,
            )

    def test_load_api_key_pool_empty(self) -> None:
        client = RichpanelClient(api_key=None)
        client._token_pool_enabled = True
        client._token_pool_secret_ids = ["id-1"]
        client._secrets_client_obj = _StubSecretsClient({})
        with self.assertRaises(SecretLoadError):
            client._load_api_key()

    def test_select_pool_key_empty(self) -> None:
        client = RichpanelClient(api_key="test-key")
        with self.assertRaises(SecretLoadError):
            client._select_pool_key([])
    def test_parse_cooldown_multiplier_negative(self) -> None:
        client = RichpanelClient(api_key="test-key")
        self.assertEqual(client._parse_cooldown_multiplier("-1"), 1.0)

    def test_load_secret_value_error(self) -> None:
        client = RichpanelClient(api_key="test-key")
        client._secrets_client_obj = _ErrorSecretsClient()
        with self.assertRaises(SecretLoadError):
            client._load_secret_value("secret")

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
