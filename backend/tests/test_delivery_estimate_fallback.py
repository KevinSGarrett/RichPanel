from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.delivery_estimate import (  # noqa: E402
    build_no_tracking_reply,
)


class DeliveryEstimateFallbackTests(unittest.TestCase):
    def test_no_tracking_reply_without_order_id(self) -> None:
        reply = build_no_tracking_reply({}, inquiry_date="2025-01-02")

        self.assertIn("We don't have tracking details available yet", reply["body"])
        self.assertIn("support agent will follow up", reply["body"])
        self.assertIsNone(reply["eta_human"])

    def test_no_tracking_reply_with_order_id(self) -> None:
        reply = build_no_tracking_reply({"order_id": "ord-1"}, inquiry_date="2025-01-02")

        self.assertIn("We don't have tracking updates yet", reply["body"])
        self.assertIn("We'll send tracking as soon as it's ready", reply["body"])
        self.assertIsNone(reply["eta_human"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
