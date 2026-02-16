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

    def test_preorder_delivery_fallback_window(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": "Pre-order Delivery",
            "order_tags_raw": "Pre-order",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
        assert reply is not None

        body = reply["body"]
        self.assertIn("marked as a pre-order", body)
        self.assertIn("scheduled to ship on Sunday, March 29, 2026", body)
        self.assertIn("(in 15 days)", body)
        self.assertIn("estimated delivery window is April 1–April 7, 2026", body)
        self.assertIn("(in 18–24 days)", body)
        self.assertIn("We'll send tracking as soon as it ships.", body)

    def test_preorder_delivery_fallback_variants(self) -> None:
        variants = ["pre order delivery", "preorder delivery"]
        for method in variants:
            with self.subTest(method=method):
                order_summary = {
                    "created_at": "2026-02-12",
                    "shipping_method": method,
                    "order_tags_raw": "Pre-order",
                }
                reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
                assert reply is not None

                body = reply["body"]
                self.assertIn("marked as a pre-order", body)
                self.assertIn(
                    "estimated delivery window is April 1–April 7, 2026", body
                )

    def test_preorder_delivery_fallback_whitespace_and_case(self) -> None:
        variants = ["  Pre-Order Delivery  ", "PRE-ORDER DELIVERY"]
        for method in variants:
            with self.subTest(method=method):
                order_summary = {
                    "created_at": "2026-02-12",
                    "shipping_method": method,
                    "order_tags_raw": "Pre-order",
                }
                reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
                assert reply is not None

                body = reply["body"]
                self.assertIn("marked as a pre-order", body)
                self.assertIn(
                    "estimated delivery window is April 1–April 7, 2026", body
                )

    def test_non_preorder_does_not_use_preorder_path(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": "Pre-order Delivery",
            "order_id": "ord-1",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
        assert reply is not None

        body = reply["body"]
        self.assertNotIn("pre-order", body.lower())
        self.assertIn("We don't have tracking updates yet", body)

    def test_preorder_missing_shipping_method_fails_closed(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": None,
            "order_tags_raw": "Pre-order",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
        assert reply is not None

        body = reply["body"]
        self.assertIn("marked as a pre-order", body)
        self.assertIn("scheduled to ship on Sunday, March 29, 2026", body)
        self.assertNotIn("estimated delivery window", body)

    def test_preorder_unknown_method_fails_closed(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": "Mystery Courier",
            "order_tags_raw": "Pre-order",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
        assert reply is not None

        body = reply["body"]
        self.assertIn("marked as a pre-order", body)
        self.assertIn("scheduled to ship on Sunday, March 29, 2026", body)
        self.assertNotIn("estimated delivery window", body)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
