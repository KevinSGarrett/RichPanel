from __future__ import annotations

import sys
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
    def __init__(self, *, response: _StubResponse):
        self._response = response

    def request(self, *args, **kwargs):
        return self._response


class _StubShopifyClient:
    def __init__(self, *, response: _StubResponse, diagnostics: dict | None = None):
        self._response = response
        self._diagnostics = diagnostics or {"status": "unknown"}

    def get_shop(self, *args, **kwargs):
        return self._response

    def token_diagnostics(self):
        return self._diagnostics


class OrderStatusPreflightCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_rp = preflight.RichpanelClient
        self._orig_shopify = preflight.ShopifyClient

    def tearDown(self) -> None:
        preflight.RichpanelClient = self._orig_rp
        preflight.ShopifyClient = self._orig_shopify

    def test_check_richpanel_pass(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=200, dry_run=False)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "PASS")

    def test_check_richpanel_dry_run_fails(self) -> None:
        preflight.RichpanelClient = lambda **kwargs: _StubRichpanelClient(  # type: ignore[assignment]
            response=_StubResponse(status_code=204, dry_run=True)
        )
        result = preflight._check_richpanel(base_url=None, api_key_secret_id=None)
        self.assertEqual(result.get("status"), "FAIL")
        self.assertIn("dry_run", result.get("details", ""))

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

    def test_refresh_lambda_config_present(self) -> None:
        result = preflight._check_refresh_lambda_config()
        self.assertIn(result.get("status"), {"PASS", "WARN"})


if __name__ == "__main__":
    raise SystemExit(unittest.main())
