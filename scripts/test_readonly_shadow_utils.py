from __future__ import annotations

import os
import unittest
from unittest import mock

import readonly_shadow_utils as utils


class _StubResponse:
    def __init__(self, status_code: int = 200, dry_run: bool = False) -> None:
        self.status_code = status_code
        self.dry_run = dry_run


class ReadonlyShadowUtilsTests(unittest.TestCase):
    def test_guard_allows_get_and_blocks_post(self) -> None:
        guard = utils.ReadOnlyHttpGuard(env_name="prod")
        guard.check(method="GET", service="richpanel", url_or_path="/v1/tickets/123")
        with self.assertRaises(utils.ReadOnlyGuardError):
            guard.check(method="POST", service="richpanel", url_or_path="/v1/tickets/123")
        self.assertEqual(len(guard.violations), 1)

    def test_redact_path_hashes_ids(self) -> None:
        path = utils._redact_path("/v1/tickets/91608")
        self.assertTrue(path.startswith("/v1/tickets/"))
        self.assertNotIn("91608", path)
        self.assertIn("redacted:", path)

    def test_guarded_richpanel_client_uses_guard(self) -> None:
        guard = utils.ReadOnlyHttpGuard(env_name="prod")
        with mock.patch.object(utils.RichpanelClient, "request", return_value=_StubResponse()) as request_mock:
            client = utils.GuardedRichpanelClient(guard=guard, dry_run=True, read_only=True)
            client.request("GET", "/v1/ping")
            request_mock.assert_called_once()
        with self.assertRaises(utils.ReadOnlyGuardError):
            client.request("POST", "/v1/tickets/123")

    def test_guarded_shopify_client_uses_guard(self) -> None:
        guard = utils.ReadOnlyHttpGuard(env_name="prod")
        with mock.patch.object(utils.ShopifyClient, "request", return_value=_StubResponse()) as request_mock:
            client = utils.GuardedShopifyClient(guard=guard, allow_network=False)
            client.request("GET", "/admin/api/2024-01/orders.json")
            request_mock.assert_called_once()
        with self.assertRaises(utils.ReadOnlyGuardError):
            client.request("POST", "/admin/api/2024-01/orders.json")


if __name__ == "__main__":
    unittest.main()
