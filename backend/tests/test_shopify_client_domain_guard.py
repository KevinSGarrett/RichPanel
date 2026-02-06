from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from integrations.shopify.client import ShopifyClient  # noqa: E402


class ShopifyClientDomainGuardTests(unittest.TestCase):
    def test_prod_requires_shop_domain(self) -> None:
        env = {"MW_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError):
                ShopifyClient()

    def test_non_prod_allows_default_domain(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, env, clear=True):
            client = ShopifyClient()
        self.assertEqual(client.shop_domain, "example.myshopify.com")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
