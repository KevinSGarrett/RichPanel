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
    _build_no_tracking_timeline_paragraph,
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
        self.assertIn("pre-order item", body)
        self.assertIn("releases on Sunday, March 29, 2026", body)
        self.assertIn("(in 15 days)", body)
        self.assertIn("processing typically takes 3-5 business days", body)
        self.assertIn("shipping takes 3-7 business days", body)
        self.assertIn("estimated for April 6–April 14, 2026", body)
        self.assertIn("about 23–31 days from today", body)
        self.assertIn(
            "(Business days are Mon–Fri; holidays may affect timelines.)", body
        )
        self.assertIn(
            "Tracking will be emailed automatically once it ships and is scanned by the carrier.",
            body,
        )

    def test_preorder_key_details_without_ship_days(self) -> None:
        delivery_estimate = {
            "preorder": True,
            "preorder_ship_date_human": "Sunday, March 29, 2026",
            "ship_days_from_inquiry_human": None,
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 7,
            "days_from_inquiry_human": "23–31 days",
            "delivery_window_human": "April 6–April 14, 2026",
            "is_late": False,
        }
        reply = build_no_tracking_reply(
            {"order_tags_raw": "Pre-order"},
            inquiry_date="2026-03-14",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None

        body = reply["body"]
        self.assertIn("releases on Sunday, March 29, 2026", body)
        self.assertNotIn("(in", body)
        self.assertIn("processing typically takes 3-5 business days", body)
        self.assertIn("shipping takes 3-7 business days", body)
        self.assertIn("estimated for April 6–April 14, 2026", body)
        self.assertIn("about 23–31 days from today", body)
        self.assertIn(
            "(Business days are Mon–Fri; holidays may affect timelines.)", body
        )

    def test_preorder_key_details_missing_processing(self) -> None:
        delivery_estimate = {
            "preorder": True,
            "preorder_ship_date_human": "Sunday, March 29, 2026",
            "ship_days_from_inquiry_human": "15 days",
            "processing_human": None,
            "transit_min_days": 3,
            "transit_max_days": 7,
            "days_from_inquiry_human": "23–31 days",
            "delivery_window_human": "April 6–April 14, 2026",
            "is_late": False,
        }
        reply = build_no_tracking_reply(
            {"order_tags_raw": "Pre-order"},
            inquiry_date="2026-03-14",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None
        body = reply["body"]
        self.assertIn("pre-order item", body)
        self.assertNotIn("processing typically takes", body)
        self.assertNotIn("estimated for April 6–April 14, 2026", body)
        self.assertNotIn("(Business days are Mon–Fri", body)
        self.assertIn(
            "Tracking will be emailed automatically once it ships and is scanned by the carrier.",
            body,
        )

    def test_preorder_key_details_empty_ship_date(self) -> None:
        delivery_estimate = {
            "preorder": True,
            "preorder_ship_date_human": "   ",
            "ship_days_from_inquiry_human": "15 days",
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 7,
            "days_from_inquiry_human": "23–31 days",
            "delivery_window_human": "April 6–April 14, 2026",
            "is_late": False,
        }
        reply = build_no_tracking_reply(
            {"order_tags_raw": "Pre-order"},
            inquiry_date="2026-03-14",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None
        body = reply["body"]
        self.assertIn("pre-order item", body)
        self.assertNotIn("releases on", body)
        self.assertIn(
            "Tracking will be emailed automatically once it ships and is scanned by the carrier.",
            body,
        )

    def test_preorder_delivery_fallback_late_any_day_now(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": "Pre-order Delivery",
            "order_tags_raw": "Pre-order",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-05-20")
        assert reply is not None

        body = reply["body"].lower()
        self.assertIn("pre-order", body)
        self.assertIn("any day now", body)
        self.assertNotIn("estimated delivery window", body)
        self.assertNotIn("key details:", body)

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
                self.assertIn("pre-order item", body)
                self.assertIn("estimated for April 6–April 14, 2026", body)

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
                self.assertIn("pre-order item", body)
                self.assertIn("estimated for April 6–April 14, 2026", body)

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
        self.assertIn("pre-order item", body)
        self.assertIn("releases on Sunday, March 29, 2026", body)
        self.assertNotIn("estimated delivery window", body)
        self.assertNotIn("Key Details:", body)

    def test_preorder_unknown_method_fails_closed(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": "Mystery Courier",
            "order_tags_raw": "Pre-order",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
        assert reply is not None

        body = reply["body"]
        self.assertIn("pre-order item", body)
        self.assertIn("releases on Sunday, March 29, 2026", body)
        self.assertNotIn("estimated delivery window", body)
        self.assertNotIn("Key Details:", body)

    def test_preorder_empty_shipping_method_fails_closed(self) -> None:
        order_summary = {
            "created_at": "2026-02-12",
            "shipping_method": "",
            "order_tags_raw": "Pre-order",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2026-03-14")
        assert reply is not None

        body = reply["body"]
        self.assertIn("pre-order item", body)
        self.assertIn("releases on Sunday, March 29, 2026", body)
        self.assertNotIn("estimated delivery window", body)
        self.assertNotIn("Key Details:", body)

    def test_no_tracking_reply_non_preorder_includes_timeline(self) -> None:
        order_summary = {
            "order_id": "12345",
            "created_at": "2024-01-01",
            "shipping_method": "Standard Shipping",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2024-01-03")
        assert reply is not None

        body = reply["body"]
        self.assertIn("processing typically takes 3-5 business days", body)
        self.assertIn("shipping takes 3-5 business days", body)
        self.assertIn("estimated for January 9–January 15, 2024", body)
        self.assertIn("about 6-10 business days total", body)
        self.assertIn(
            "(Business days are Mon–Fri; holidays may affect timelines.)", body
        )

    def test_no_tracking_key_details_missing_processing(self) -> None:
        delivery_estimate = {
            "preorder": False,
            "order_created_date": "2024-01-01",
            "bucket": "Standard",
            "normalized_method": "Standard (3-5 business days)",
            "raw_method": "Standard Shipping",
            "eta_human": "4-8 business days",
            "is_late": False,
            "processing_human": None,
            "transit_min_days": 3,
            "transit_max_days": 5,
            "window_min_days": 6,
            "window_max_days": 10,
            "delivery_window_human": "January 9–January 15, 2024",
        }
        reply = build_no_tracking_reply(
            {"order_id": "12345", "created_at": "2024-01-01", "shipping_method": "Standard"},
            inquiry_date="2024-01-03",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None
        body = reply["body"]
        self.assertNotIn("processing typically takes", body)
        self.assertNotIn("estimated for January 9–January 15, 2024", body)
        self.assertNotIn(
            "(Business days are Mon–Fri; holidays may affect timelines.)", body
        )

    def test_build_timeline_paragraph_non_preorder_bucket(self) -> None:
        estimate = {
            "bucket": "Standard",
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 5,
            "window_min_days": 6,
            "window_max_days": 10,
            "delivery_window_human": "January 9–January 15, 2024",
            "preorder": False,
        }
        paragraph = _build_no_tracking_timeline_paragraph(estimate)
        assert paragraph is not None
        self.assertIn("For Standard shipping,", paragraph)
        self.assertIn("processing typically takes 3-5 business days", paragraph)
        self.assertIn("shipping takes 3-5 business days", paragraph)
        self.assertIn("about 6-10 business days total", paragraph)

    def test_build_timeline_paragraph_preorder(self) -> None:
        estimate = {
            "bucket": "Standard",
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 7,
            "delivery_window_human": "April 6–April 14, 2026",
            "days_from_inquiry_human": "23–31 days",
            "preorder": True,
        }
        paragraph = _build_no_tracking_timeline_paragraph(estimate)
        assert paragraph is not None
        self.assertIn("For Standard shipping,", paragraph)
        self.assertIn("after release, processing typically takes 3-5 business days", paragraph)
        self.assertIn("shipping takes 3-7 business days", paragraph)
        self.assertIn("about 23–31 days from today", paragraph)

    def test_build_timeline_paragraph_preorder_no_days_from_today(self) -> None:
        estimate = {
            "bucket": "Standard",
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 7,
            "delivery_window_human": "April 6–April 14, 2026",
            "preorder": True,
        }
        paragraph = _build_no_tracking_timeline_paragraph(estimate)
        assert paragraph is not None
        self.assertIn("after release, processing typically takes 3-5 business days", paragraph)
        self.assertIn("(Business days are Mon–Fri; holidays may affect timelines.)", paragraph)

    def test_build_timeline_paragraph_blank_window_returns_none(self) -> None:
        estimate = {
            "bucket": "Standard",
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 7,
            "delivery_window_human": "   ",
        }
        assert _build_no_tracking_timeline_paragraph(estimate) is None

    def test_build_timeline_paragraph_missing_method_uses_fallback(self) -> None:
        estimate = {
            "processing_human": "3-5 business days",
            "transit_min_days": 3,
            "transit_max_days": 7,
            "window_min_days": 6,
            "window_max_days": 10,
            "delivery_window_human": "January 9–January 15, 2024",
            "preorder": False,
        }
        paragraph = _build_no_tracking_timeline_paragraph(
            estimate, fallback_method=None
        )
        assert paragraph is not None
        self.assertIn("With your shipping method,", paragraph)

    def test_build_timeline_paragraph_missing_transit_returns_none(self) -> None:
        estimate = {
            "processing_human": "3-5 business days",
            "transit_min_days": None,
            "transit_max_days": 7,
            "delivery_window_human": "January 9–January 15, 2024",
        }
        assert _build_no_tracking_timeline_paragraph(estimate) is None

    def test_no_tracking_key_details_missing_transit(self) -> None:
        delivery_estimate = {
            "preorder": False,
            "order_created_date": "2024-01-01",
            "bucket": "Standard",
            "normalized_method": "Standard (3-5 business days)",
            "raw_method": "Standard Shipping",
            "eta_human": "4-8 business days",
            "is_late": False,
            "processing_human": "3-5 business days",
            "transit_min_days": None,
            "transit_max_days": None,
            "window_min_days": 6,
            "window_max_days": 10,
            "delivery_window_human": "January 9–January 15, 2024",
        }
        reply = build_no_tracking_reply(
            {"order_id": "12345", "created_at": "2024-01-01", "shipping_method": "Standard"},
            inquiry_date="2024-01-03",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None
        body = reply["body"]
        self.assertNotIn("shipping takes", body)
        self.assertNotIn("estimated for January 9–January 15, 2024", body)

    def test_no_tracking_reply_non_preorder_late_no_key_details(self) -> None:
        order_summary = {
            "order_id": "late-1",
            "created_at": "2024-01-01",
            "shipping_method": "Standard Shipping (3-5 business days)",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2024-01-16")
        assert reply is not None
        body_lower = reply["body"].lower()
        self.assertIn("any day now", body_lower)
        self.assertNotIn("key details:", body_lower)
        self.assertNotIn(
            "(Business days are Mon–Fri; holidays may affect timelines.)",
            reply["body"],
        )

    def test_no_tracking_reply_missing_window_no_key_details(self) -> None:
        delivery_estimate = {
            "preorder": False,
            "order_created_date": "2024-01-01",
            "bucket": "Standard",
            "normalized_method": "Standard (3-5 business days)",
            "raw_method": "Standard Shipping",
            "eta_human": "1-2 business days",
            "is_late": False,
            "processing_human": "3-5 business days",
            "delivery_window_human": None,
        }
        reply = build_no_tracking_reply(
            {"order_id": "12345", "created_at": "2024-01-01", "shipping_method": "Standard"},
            inquiry_date="2024-01-03",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None
        self.assertNotIn("(Business days are Mon–Fri", reply["body"])

    def test_no_tracking_reply_whitespace_window_no_key_details(self) -> None:
        delivery_estimate = {
            "preorder": False,
            "order_created_date": "2024-01-01",
            "bucket": "Standard",
            "normalized_method": "Standard (3-5 business days)",
            "raw_method": "Standard Shipping",
            "eta_human": "1-2 business days",
            "is_late": False,
            "processing_human": "3-5 business days",
            "delivery_window_human": "   ",
        }
        reply = build_no_tracking_reply(
            {"order_id": "12345", "created_at": "2024-01-01", "shipping_method": "Standard"},
            inquiry_date="2024-01-03",
            delivery_estimate=delivery_estimate,
        )
        assert reply is not None
        self.assertNotIn("(Business days are Mon–Fri", reply["body"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
