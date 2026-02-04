import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest import mock

import shopify_health_check as health_check


class _StubClient:
    def __init__(self, client_id, client_secret):
        self._client_id = client_id
        self._client_secret = client_secret

    def _load_client_credentials(self):
        return self._client_id, self._client_secret


class ShopifyHealthCheckTests(unittest.TestCase):
    def test_safe_token_format(self) -> None:
        self.assertEqual(health_check._safe_token_format(None), "unknown")
        self.assertEqual(health_check._safe_token_format("json"), "json")
        self.assertEqual(health_check._safe_token_format("plain"), "raw")

    def test_classify_status(self) -> None:
        status, hint = health_check._classify_status(200, False)
        self.assertEqual(status, "PASS")
        self.assertIsNone(hint)

        status, hint = health_check._classify_status(401, False)
        self.assertEqual(status, "FAIL_INVALID_TOKEN")
        self.assertIsNotNone(hint)

        status, hint = health_check._classify_status(403, False)
        self.assertEqual(status, "FAIL_FORBIDDEN")
        self.assertIsNotNone(hint)

        status, hint = health_check._classify_status(429, False)
        self.assertEqual(status, "FAIL_RATE_LIMIT")
        self.assertIsNotNone(hint)

        status, hint = health_check._classify_status(None, True)
        self.assertEqual(status, "DRY_RUN")
        self.assertIsNone(hint)

    def test_load_client_credentials(self) -> None:
        client = _StubClient("id", "secret")
        has_id, has_secret = health_check._load_client_credentials(client)
        self.assertTrue(has_id)
        self.assertTrue(has_secret)

        client = _StubClient(None, None)
        has_id, has_secret = health_check._load_client_credentials(client)
        self.assertFalse(has_id)
        self.assertFalse(has_secret)

    def test_load_client_credentials_exception(self) -> None:
        class _ErrorClient:
            def _load_client_credentials(self):
                raise RuntimeError("boom")

        has_id, has_secret = health_check._load_client_credentials(_ErrorClient())
        self.assertFalse(has_id)
        self.assertFalse(has_secret)

    def test_write_json(self) -> None:
        payload = {"b": 2, "a": 1}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            health_check._write_json(path, payload)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data, payload)

    def test_main_passes_with_stub_client(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = False
            reason = None
            url = "https://example.myshopify.com/admin/api/2024-01/shop.json"

        class _StubClient:
            environment = "prod"
            shop_domain = "example.myshopify.com"
            _secret_id_candidates = ["rp-mw/prod/shopify/admin_api_token"]
            refresh_enabled = True

            def refresh_access_token(self):
                return True

            def get_shop(self, safe_mode=False, automation_enabled=True):
                return _StubResponse()

            def token_diagnostics(self):
                return {
                    "status": "loaded",
                    "token_type": "offline",
                    "raw_format": "json",
                    "has_refresh_token": True,
                    "expires_at": 123,
                    "expired": False,
                }

            def _load_client_credentials(self):
                return "id", "secret"

            def refresh_error(self):
                return None

        with tempfile.TemporaryDirectory() as tmp:
            out_path = str(Path(tmp) / "out.json")
            with mock.patch.object(
                health_check, "ShopifyClient", return_value=_StubClient()
            ):
                with mock.patch.object(
                    health_check.sys,
                    "argv",
                    [
                        "shopify_health_check.py",
                        "--out-json",
                        out_path,
                        "--refresh",
                        "--env",
                        "prod",
                        "--aws-region",
                        "us-east-2",
                        "--verbose",
                    ],
                ):
                    exit_code = health_check.main()
            self.assertEqual(exit_code, 0)

    def test_main_dry_run_returns_nonzero(self) -> None:
        class _StubResponse:
            status_code = 0
            dry_run = True
            reason = "missing_access_token"

        class _StubClient:
            environment = "prod"
            shop_domain = "example.myshopify.com"
            _secret_id_candidates = ["rp-mw/prod/shopify/admin_api_token"]
            refresh_enabled = False

            def refresh_access_token(self):
                return False

            def get_shop(self, safe_mode=False, automation_enabled=True):
                return _StubResponse()

            def token_diagnostics(self):
                return {"status": "unknown"}

            def _load_client_credentials(self):
                return None, None

            def refresh_error(self):
                return None

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(
                health_check, "ShopifyClient", return_value=_StubClient()
            ):
                with mock.patch.object(
                    health_check.sys,
                    "argv",
                    ["shopify_health_check.py", "--refresh-dry-run"],
                ):
                    exit_code = health_check.main()
        self.assertNotEqual(exit_code, 0)

    def test_main_records_body_excerpt_on_failure(self) -> None:
        class _StubResponse:
            status_code = 401
            dry_run = False
            reason = None
            url = "https://example.myshopify.com/admin/api/2024-01/shop.json"
            body = b'{"errors":"invalid token"}'

        class _StubClient:
            environment = "prod"
            shop_domain = "example.myshopify.com"
            _secret_id_candidates = ["rp-mw/prod/shopify/admin_api_token"]
            refresh_enabled = False

            def refresh_access_token(self):
                return False

            def get_shop(self, safe_mode=False, automation_enabled=True):
                return _StubResponse()

            def token_diagnostics(self):
                return {
                    "status": "loaded",
                    "token_type": "offline",
                    "raw_format": "json",
                    "has_refresh_token": False,
                    "expires_at": None,
                    "expired": None,
                }

            def _load_client_credentials(self):
                return None, None

            def refresh_error(self):
                return "missing_refresh_token"

        with tempfile.TemporaryDirectory() as tmp:
            out_path = str(Path(tmp) / "out.json")
            with mock.patch.object(
                health_check, "ShopifyClient", return_value=_StubClient()
            ):
                with mock.patch.object(
                    health_check.sys,
                    "argv",
                    [
                        "shopify_health_check.py",
                        "--out-json",
                        out_path,
                    ],
                ):
                    exit_code = health_check.main()
            payload = json.loads(Path(out_path).read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload.get("status"), "FAIL_INVALID_TOKEN")
        self.assertIn("invalid token", payload["health_check"]["body_excerpt"])


if __name__ == "__main__":
    unittest.main()
