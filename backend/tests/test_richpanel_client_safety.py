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

from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelClient,
    RichpanelWriteDisabledError,
)


class RichpanelClientSafetyTests(unittest.TestCase):
    def _make_client(self) -> tuple[RichpanelClient, mock.Mock]:
        transport = mock.Mock()
        transport.send.side_effect = AssertionError(
            "transport.send should not be called during safety checks"
        )
        return RichpanelClient(transport=transport), transport

    def test_prod_default_read_only_blocks_writes(self) -> None:
        with mock.patch.dict(os.environ, {"RICHPANEL_ENV": "prod"}, clear=True):
            client, transport = self._make_client()
            self.assertTrue(client.read_only)

            for method in ("POST", "PUT", "PATCH", "DELETE"):
                with self.subTest(method=method):
                    with self.assertRaises(RichpanelWriteDisabledError):
                        client.request(
                            method, "/v1/tickets", json_body={"ticket_id": "t-1"}
                        )

            transport.send.assert_not_called()

    def test_read_only_env_override_allows_false_but_write_disabled_blocks(self) -> None:
        env = {
            "RICHPANEL_ENV": "prod",
            "RICHPANEL_READ_ONLY": "0",
            "RICHPANEL_WRITE_DISABLED": "1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            client, transport = self._make_client()
            self.assertFalse(client.read_only)

            with self.assertRaises(RichpanelWriteDisabledError):
                client.request("POST", "/v1/tickets", json_body={"ticket_id": "t-2"})

            transport.send.assert_not_called()

    def test_dry_run_does_not_bypass_write_disabled(self) -> None:
        env = {
            "RICHPANEL_ENV": "local",
            "RICHPANEL_READ_ONLY": "0",
            "RICHPANEL_WRITE_DISABLED": "1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            client, transport = self._make_client()
            self.assertFalse(client.read_only)

            with self.assertRaises(RichpanelWriteDisabledError):
                client.request(
                    "POST",
                    "/v1/tickets",
                    json_body={"ticket_id": "t-3"},
                    dry_run=True,
                )

            transport.send.assert_not_called()


if __name__ == "__main__":
    raise SystemExit(unittest.main())
