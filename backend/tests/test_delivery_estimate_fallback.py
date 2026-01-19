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
        assert reply is not None

        self.assertIn("We don't have tracking details available yet", reply["body"])
        self.assertIn("support agent will follow up", reply["body"])
        self.assertIsNone(reply["eta_human"])

    def test_no_tracking_reply_with_order_id(self) -> None:
        reply = build_no_tracking_reply(
            {"order_id": "ord-1"}, inquiry_date="2025-01-02"
        )
        assert reply is not None

        self.assertIn("We don't have tracking updates yet", reply["body"])
        self.assertIn("We'll send tracking as soon as it's ready", reply["body"])
        self.assertIsNone(reply["eta_human"])

    def test_build_no_tracking_reply_none_order_summary(self) -> None:
        reply = build_no_tracking_reply(None, inquiry_date="2025-01-02")
        assert reply is not None

        self.assertIn(
            "we don't have tracking details available yet", reply["body"].lower()
        )
        self.assertNotIn("we have order", reply["body"].lower())

    def test_build_no_tracking_reply_order_id_is_none(self) -> None:
        reply = build_no_tracking_reply({"order_id": None}, inquiry_date="2025-01-02")
        assert reply is not None

        self.assertIn(
            "we don't have tracking details available yet", reply["body"].lower()
        )


if __name__ == "__main__":
    raise SystemExit(unittest.main())
