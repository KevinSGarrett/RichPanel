from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import timedelta
from unittest import mock
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import order_status_preflight_check as preflight  # noqa: E402


class _StubResponse:
    def __init__(self, *, status_code: int, dry_run: bool = False, reason: str | None = None):
        self.status_code = status_code
        self.dry_run = dry_run
        self.reason = reason


class _StubRichpanelClient:
    def __init__(self, *, response: _StubResponse | None = None, exc: Exception | None = None):
        self._response = response
        self._exc = exc

    def request(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return self._response


class _CaptureRichpanelClient:
    def __init__(self, *, response: _StubResponse | None = None):
        self._response = response or _StubResponse(status_code=200, dry_run=False)
        self.requested_path: str | None = None

    def request(self, _method: str, path: str, **_kwargs):
        self.requested_path = path
        return self._response


class _StubShopifyClient:
    def __init__(self, *, response: _StubResponse | None = None, diagnostics: dict | None = None, exc: Exception | None = None):
        self._response = response
        self._diagnostics = diagnostics or {"status": "unknown"}
        self._exc = exc

    def get_shop(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return self._response

    def token_diagnostics(self):
        return self._diagnostics


class _StubTransport:
    def __init__(self, *, response=None, exc: Exception | None = None):
        self._response = response
        self._exc = exc

    def send(self, _request):
        if self._exc is not None:
            raise self._exc
        return self._response


class _StubShopifyGraphqlClient:
    def __init__(
        self,
        *,
        token: str | None,
        response=None,
        exc: Exception | None = None,
    ):
        self._token = token
        self.transport = _StubTransport(response=response, exc=exc)
        self.timeout_seconds = 5

    def _load_access_token(self):
        return self._token, "stub_reason"

    def _build_url(self, path: str, _version: str | None):
        return f"https://example.myshopify.com/{path}"


class _StubSecretsClient:
    def __init__(self, *, fail_ids=None):
        self._fail_ids = set(fail_ids or [])

    def get_secret_value(self, *, SecretId: str):
        if SecretId in self._fail_ids:
            raise RuntimeError("missing")
        return {"SecretString": "ok"}


class _StubLogsClient:
    def __init__(self, *, streams=None, events_by_stream=None, raise_describe_exc=None):
        self._streams = streams or []
        self._events_by_stream = events_by_stream or {}
        self._raise_describe_exc = raise_describe_exc

    def describe_log_streams(self, **_kwargs):
        if self._raise_describe_exc is not None:
            raise self._raise_describe_exc
        return {"logStreams": self._streams}

    def get_log_events(self, *, logStreamName: str, **_kwargs):
        return {"events": self._events_by_stream.get(logStreamName, [])}


class _StubBoto3:
    def __init__(self, client):
        self._client = client

    def client(self, _name: str):
        return self._client


class _StubSession:
    def __init__(self, client):
        self._client = client

    def client(self, _name: str):
        return self._client


class OrderStatusPreflightCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_rp = preflight.RichpanelClient
        self._orig_shopify = preflight.ShopifyClient
        self._orig_boto3 = preflight.boto3

    def tearDown(self) -> None:
        preflight.RichpanelClient = self._orig_rp
        preflight.ShopifyClient = self._orig_shopify
        preflight.boto3 = self._orig_boto3

    def test_check_richpanel_pass(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=200, dry_run=False)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "PASS")

    def test_check_richpanel_honors_preflight_path_env(self) -> None:
        capture = _CaptureRichpanelClient()
        preflight.RichpanelClient = lambda **kwargs: capture  # type: ignore[assignment]
        with mock.patch.dict(os.environ, {"RICHPANEL_PREFLIGHT_PATH": "/v1/users"}, clear=True):
            result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "PASS")
        self.assertEqual(capture.requested_path, "/v1/users")

    def test_check_richpanel_dry_run_fails(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=204, dry_run=True)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("dry_run", result.get("details", ""))

    def test_check_richpanel_auth_and_rate_limit(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=401, dry_run=False)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("auth_fail", result.get("details", ""))

        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=429, dry_run=False)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("rate_limited", result.get("details", ""))

        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=500, dry_run=False)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("http_error", result.get("details", ""))

    def test_check_richpanel_exception(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            exc=preflight.RichpanelRequestError("boom")
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("request_failed", result.get("details", ""))

        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            exc=RuntimeError("boom")
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("request_failed", result.get("details", ""))

    def test_check_shopify_dry_run_fails(self) -> None:
        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=0, dry_run=True, reason="secret_lookup_failed")
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("dry_run", result.get("details", ""))
        self.assertIn("token_diagnostics", result)

    def test_check_shopify_pass(self) -> None:
        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=200, dry_run=False),
            diagnostics={"status": "loaded"},
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "PASS")

    def test_check_shopify_auth_rate_limit_http_error(self) -> None:
        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=401, dry_run=False),
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("auth_fail", result.get("details", ""))

        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=429, dry_run=False),
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("rate_limited", result.get("details", ""))

        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=500, dry_run=False),
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("http_error", result.get("details", ""))

    def test_check_shopify_exception(self) -> None:
        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            exc=preflight.ShopifyRequestError("boom")
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("request_failed", result.get("details", ""))

    def test_check_shopify_graphql_missing_token(self) -> None:
        preflight.ShopifyClient = (  # type: ignore[assignment]
            lambda **_kwargs: _StubShopifyGraphqlClient(token=None)
        )
        result = preflight._check_shopify_graphql(
            shop_domain="example.myshopify.com",
            access_token_secret_id="secret",
        )
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("missing_token", result.get("details", ""))

    def test_check_shopify_graphql_pass(self) -> None:
        response = _StubResponse(status_code=200)
        response.body = b"{\"data\": {\"shop\": {\"name\": \"Demo\"}}}"  # type: ignore[attr-defined]
        preflight.ShopifyClient = (  # type: ignore[assignment]
            lambda **_kwargs: _StubShopifyGraphqlClient(
                token="token", response=response
            )
        )
        result = preflight._check_shopify_graphql(
            shop_domain="example.myshopify.com",
            access_token_secret_id="secret",
        )
        self.assertEqual(result.get("status"), "PASS")

    def test_check_shopify_graphql_errors(self) -> None:
        response = _StubResponse(status_code=200)
        response.body = b"{\"errors\": [{\"message\": \"bad\"}]}"  # type: ignore[attr-defined]
        preflight.ShopifyClient = (  # type: ignore[assignment]
            lambda **_kwargs: _StubShopifyGraphqlClient(
                token="token", response=response
            )
        )
        result = preflight._check_shopify_graphql(
            shop_domain="example.myshopify.com",
            access_token_secret_id="secret",
        )
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("graphql_errors", result.get("details", ""))

    def test_check_shopify_graphql_auth_fail(self) -> None:
        response = _StubResponse(status_code=401)
        response.body = b"{}"  # type: ignore[attr-defined]
        preflight.ShopifyClient = (  # type: ignore[assignment]
            lambda **_kwargs: _StubShopifyGraphqlClient(
                token="token", response=response
            )
        )
        result = preflight._check_shopify_graphql(
            shop_domain="example.myshopify.com",
            access_token_secret_id="secret",
        )
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("auth_fail", result.get("details", ""))

    def test_check_shopify_graphql_exception(self) -> None:
        preflight.ShopifyClient = (  # type: ignore[assignment]
            lambda **_kwargs: _StubShopifyGraphqlClient(
                token="token", exc=RuntimeError("boom")
            )
        )
        result = preflight._check_shopify_graphql(
            shop_domain="example.myshopify.com",
            access_token_secret_id="secret",
        )
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("request_failed", result.get("details", ""))

    def test_check_required_env_fail_and_pass(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = preflight._check_required_env()
            self.assertEqual(result.get("status"), "FAIL")
            self.assertIn("missing", result.get("details", ""))
        with mock.patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "prod",
                "MW_ALLOW_NETWORK_READS": "true",
                "RICHPANEL_READ_ONLY": "true",
                "RICHPANEL_WRITE_DISABLED": "true",
                "RICHPANEL_OUTBOUND_ENABLED": "false",
                "SHOPIFY_OUTBOUND_ENABLED": "true",
                "SHOPIFY_WRITE_DISABLED": "true",
                "SHOPIFY_SHOP_DOMAIN": "example.myshopify.com",
            },
            clear=True,
        ):
            result = preflight._check_required_env()
            self.assertEqual(result.get("status"), "PASS")

    def test_check_secrets_paths(self) -> None:
        preflight.boto3 = _StubBoto3(_StubSecretsClient())
        result = preflight._check_secrets(env_name="prod")
        self.assertEqual(result.get("status"), "PASS")
        preflight.boto3 = _StubBoto3(
            _StubSecretsClient(fail_ids={"rp-mw/prod/richpanel/api_key"})
        )
        result = preflight._check_secrets(env_name="prod")
        self.assertEqual(result.get("status"), "FAIL")

    def test_check_secrets_boto3_missing(self) -> None:
        preflight.boto3 = None
        result = preflight._check_secrets(env_name="prod")
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("boto3_unavailable", result.get("details", ""))

    def test_check_bot_agent_id_secret_warns_in_dev(self) -> None:
        preflight.boto3 = _StubBoto3(
            _StubSecretsClient(fail_ids={"rp-mw/dev/richpanel/bot_agent_id"})
        )
        result = preflight._check_bot_agent_id_secret(env_name="dev")
        self.assertEqual(result.get("status"), "WARN")
        self.assertFalse(result.get("present"))

    def test_check_bot_agent_id_secret_fails_in_prod(self) -> None:
        preflight.boto3 = _StubBoto3(
            _StubSecretsClient(fail_ids={"rp-mw/prod/richpanel/bot_agent_id"})
        )
        result = preflight._check_bot_agent_id_secret(env_name="prod")
        self.assertEqual(result.get("status"), "FAIL")
        self.assertFalse(result.get("present"))

    def test_check_bot_agent_id_secret_passes_when_present(self) -> None:
        preflight.boto3 = _StubBoto3(_StubSecretsClient())
        result = preflight._check_bot_agent_id_secret(env_name="prod")
        self.assertEqual(result.get("status"), "PASS")
        self.assertTrue(result.get("present"))

    def test_check_bot_agent_id_secret_boto3_missing(self) -> None:
        preflight.boto3 = None
        result = preflight._check_bot_agent_id_secret(env_name="prod")
        self.assertEqual(result.get("status"), "FAIL")
        self.assertFalse(result.get("present"))

    def test_check_bot_agent_id_secret_uses_session(self) -> None:
        session = _StubSession(_StubSecretsClient())
        preflight.boto3 = _StubBoto3(_StubSecretsClient())
        result = preflight._check_bot_agent_id_secret(env_name="prod", session=session)
        self.assertEqual(result.get("status"), "PASS")
        self.assertTrue(result.get("present"))

    def test_check_secrets_uses_session(self) -> None:
        session = _StubSession(_StubSecretsClient())
        preflight.boto3 = _StubBoto3(_StubSecretsClient())
        result = preflight._check_secrets(env_name="prod", session=session)
        self.assertEqual(result.get("status"), "PASS")

    def test_refresh_lambda_last_success(self) -> None:
        now = preflight.datetime.now(preflight.timezone.utc)
        ts_ms = int((now - timedelta(hours=1)).timestamp() * 1000)
        logs_client = _StubLogsClient(
            streams=[{"logStreamName": "stream-1"}],
            events_by_stream={
                "stream-1": [
                    {"timestamp": ts_ms, "message": "{\"refresh_succeeded\": true}"}
                ]
            },
        )
        preflight.boto3 = _StubBoto3(logs_client)
        result = preflight._check_refresh_lambda_last_success(env_name="prod")
        self.assertEqual(result.get("status"), "PASS")

    def test_refresh_lambda_last_success_missing(self) -> None:
        logs_client = _StubLogsClient(streams=[{"logStreamName": "stream-1"}])
        preflight.boto3 = _StubBoto3(logs_client)
        result = preflight._check_refresh_lambda_last_success(env_name="prod")
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("no_success_event_found", result.get("details", ""))

    def test_refresh_lambda_last_success_refresh_disabled(self) -> None:
        now = preflight.datetime.now(preflight.timezone.utc)
        ts_ms = int((now - timedelta(hours=2)).timestamp() * 1000)
        logs_client = _StubLogsClient(
            streams=[{"logStreamName": "stream-1"}],
            events_by_stream={
                "stream-1": [
                    {
                        "timestamp": ts_ms,
                        "message": "{\"refresh_attempted\": false, \"refresh_error\": \"refresh_disabled\"}",
                    }
                ]
            },
        )
        preflight.boto3 = _StubBoto3(logs_client)
        result = preflight._check_refresh_lambda_last_success(env_name="prod")
        self.assertEqual(result.get("status"), "WARN")
        self.assertIn("refresh_disabled", result.get("details", ""))

    def test_refresh_lambda_last_success_logs_error(self) -> None:
        logs_client = _StubLogsClient(raise_describe_exc=RuntimeError("boom"))
        preflight.boto3 = _StubBoto3(logs_client)
        result = preflight._check_refresh_lambda_last_success(env_name="prod")
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("log_query_failed", result.get("details", ""))

    def test_refresh_lambda_last_success_missing_logs_warns_in_dev(self) -> None:
        original_client_error = preflight.ClientError
        try:
            class _StubClientError(Exception):
                def __init__(self, code: str) -> None:
                    super().__init__("stub")
                    self.response = {"Error": {"Code": code, "Message": "missing"}}

            preflight.ClientError = _StubClientError  # type: ignore[assignment]
            error = _StubClientError("ResourceNotFoundException")
            logs_client = _StubLogsClient(raise_describe_exc=error)
            preflight.boto3 = _StubBoto3(logs_client)
            result = preflight._check_refresh_lambda_last_success(env_name="dev")
            self.assertEqual(result.get("status"), "WARN")
            self.assertIn("log_query_failed", result.get("details", ""))
        finally:
            preflight.ClientError = original_client_error

    def test_refresh_lambda_last_success_missing_logs_fails_in_prod(self) -> None:
        original_client_error = preflight.ClientError
        try:
            class _StubClientError(Exception):
                def __init__(self, code: str) -> None:
                    super().__init__("stub")
                    self.response = {"Error": {"Code": code, "Message": "missing"}}

            preflight.ClientError = _StubClientError  # type: ignore[assignment]
            error = _StubClientError("ResourceNotFoundException")
            logs_client = _StubLogsClient(raise_describe_exc=error)
            preflight.boto3 = _StubBoto3(logs_client)
            result = preflight._check_refresh_lambda_last_success(env_name="prod")
            self.assertEqual(result.get("status"), "FAIL")
            self.assertIn("log_query_failed", result.get("details", ""))
        finally:
            preflight.ClientError = original_client_error

        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            exc=RuntimeError("boom")
        )
        result = preflight._check_shopify(shop_domain=None, access_token_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("request_failed", result.get("details", ""))

    def test_refresh_lambda_config_present(self) -> None:
        result = preflight._check_refresh_lambda_config()
        self.assertIn(result.get("status"), {"PASS", "WARN"})

    def test_refresh_lambda_config_warn(self) -> None:
        original_root = preflight.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            infra_dir = Path(tmpdir) / "infra" / "cdk" / "lib"
            infra_dir.mkdir(parents=True, exist_ok=True)
            (infra_dir / "richpanel-middleware-stack.ts").write_text(
                "// no refresh lambda here\n", encoding="utf-8"
            )
            preflight.ROOT = Path(tmpdir)
            result = preflight._check_refresh_lambda_config()
            self.assertEqual(result.get("status"), "WARN")
        preflight.ROOT = original_root

    def test_refresh_lambda_config_missing(self) -> None:
        original_root = preflight.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            preflight.ROOT = Path(tmpdir)
            result = preflight._check_refresh_lambda_config()
            self.assertEqual(result.get("status"), "SKIP")
        preflight.ROOT = original_root

    def test_write_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.md"
            payload = {
                "timestamp_utc": "2026-02-02T00:00:00Z",
                "overall_status": "PASS",
                "bot_agent_id_secret_present": True,
                "checks": [
                    {
                        "name": "richpanel_api",
                        "status": "PASS",
                        "details": "ok",
                        "next_action": "none",
                    }
                ],
                "shopify_token_diagnostics": {"status": "loaded"},
            }
            preflight._write_markdown(path, payload)
            content = path.read_text(encoding="utf-8")
            self.assertIn("Order status preflight health check", content)
            self.assertIn("Shopify token diagnostics", content)

    def test_write_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.json"
            payload = {"overall_status": "PASS", "checks": []}
            preflight._write_json(path, payload)
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed.get("overall_status"), "PASS")

    def test_main_success_path(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=200, dry_run=False)
        )
        preflight.ShopifyClient = lambda **kwargs: _StubShopifyClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=200, dry_run=False)
        )
        argv = [
            "order_status_preflight_check.py",
            "--skip-refresh-lambda-check",
            "--skip-secrets-check",
        ]
        with mock.patch.object(preflight, "_check_shopify_graphql", return_value={"status": "PASS", "details": "ok"}), mock.patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "dev",
                "MW_ALLOW_NETWORK_READS": "true",
                "RICHPANEL_READ_ONLY": "true",
                "RICHPANEL_WRITE_DISABLED": "true",
                "RICHPANEL_OUTBOUND_ENABLED": "false",
                "SHOPIFY_OUTBOUND_ENABLED": "true",
                "SHOPIFY_WRITE_DISABLED": "true",
                "SHOPIFY_SHOP_DOMAIN": "example.myshopify.com",
            },
            clear=False,
        ), mock.patch.object(sys, "argv", argv):
            self.assertEqual(preflight.main(), 0)

    def test_main_env_and_output_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_md = Path(tmpdir) / "proof.md"
            with mock.patch.object(
                preflight, "_check_richpanel", return_value={"status": "FAIL", "details": "bad", "next_action": "fix"}
            ), mock.patch.object(
                preflight, "_check_shopify", return_value={"status": "PASS", "details": "ok"}
            ), mock.patch.object(
                preflight, "_check_refresh_lambda_config", return_value={"status": "PASS", "details": "lambda"}
            ):
                argv = [
                    "order_status_preflight_check.py",
                    "--env",
                    "dev",
                    "--skip-refresh-lambda-check",
                    "--skip-secrets-check",
                    "--out-md",
                    str(out_md),
                ]
                old_env = os.environ.get("ENVIRONMENT")
                try:
                    with mock.patch.object(
                        preflight,
                        "_check_shopify_graphql",
                        return_value={"status": "PASS", "details": "ok"},
                    ), mock.patch.dict(
                        os.environ,
                        {
                            "MW_ALLOW_NETWORK_READS": "true",
                            "RICHPANEL_READ_ONLY": "true",
                            "RICHPANEL_WRITE_DISABLED": "true",
                            "RICHPANEL_OUTBOUND_ENABLED": "false",
                            "SHOPIFY_OUTBOUND_ENABLED": "true",
                            "SHOPIFY_WRITE_DISABLED": "true",
                            "SHOPIFY_SHOP_DOMAIN": "example.myshopify.com",
                        },
                        clear=False,
                    ), mock.patch.object(sys, "argv", argv):
                        self.assertEqual(preflight.main(), 2)
                finally:
                    if old_env is None:
                        os.environ.pop("ENVIRONMENT", None)
                    else:
                        os.environ["ENVIRONMENT"] = old_env
            self.assertTrue(out_md.exists())


if __name__ == "__main__":
    raise SystemExit(unittest.main())
