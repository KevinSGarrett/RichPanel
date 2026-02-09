from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.delivery_estimate import (  # noqa: E402
    build_carrier_tracking_url,
    build_tracking_reply,
)


class TrackingLinkGenerationTests(unittest.TestCase):
    def test_fedex_tracking_url(self) -> None:
        url = build_carrier_tracking_url("FedEx", "TEST123")
        assert url is not None
        self.assertIn("fedextrack", url)
        self.assertIn("TEST123", url)

    def test_ups_tracking_url(self) -> None:
        url = build_carrier_tracking_url("UPS Ground", "UPS123")
        assert url is not None
        self.assertIn("ups.com/track", url)
        self.assertIn("tracknum=UPS123", url)

    def test_usps_tracking_url(self) -> None:
        url = build_carrier_tracking_url("USPS Priority", "USPS123")
        assert url is not None
        self.assertIn("TrackConfirmAction", url)
        self.assertIn("tLabels=USPS123", url)

    def test_dhl_tracking_url(self) -> None:
        url = build_carrier_tracking_url("DHL Express", "DHL123")
        assert url is not None
        self.assertIn("tracking-express", url)
        self.assertIn("tracking-id=DHL123", url)

    def test_existing_tracking_url_is_unchanged(self) -> None:
        summary = {
            "carrier": "FedEx",
            "tracking_number": "TEST123",
            "tracking_url": "https://example.com/track?x=1",
        }
        reply = build_tracking_reply(summary)
        assert reply is not None
        self.assertEqual(
            summary["tracking_url"], "https://example.com/track?x=1"
        )
        self.assertIn("https://example.com/track?x=1", reply["body"])

    def test_unknown_carrier_fallback(self) -> None:
        summary = {"carrier": "Local Courier", "tracking_number": "TEST123"}
        reply = build_tracking_reply(summary)
        assert reply is not None
        self.assertIn("Tracking link: (not available)", reply["body"])
        self.assertIsNone(build_carrier_tracking_url("Local Courier", "TEST123"))


if __name__ == "__main__":
    raise SystemExit(unittest.main())