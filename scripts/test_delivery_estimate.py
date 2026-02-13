from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.delivery_estimate import (  # noqa: E402
    add_business_days,
    build_no_tracking_reply,
    build_tracking_reply,
    build_tracking_url,
    business_days_between,
    compute_delivery_estimate,
    compute_preorder_delivery_estimate,
    has_preorder_tag,
    normalize_shipping_method,
    parse_transit_days,
    _format_delivery_window,
    _format_day_window,
)


class DeliveryEstimateTests(unittest.TestCase):
    def test_business_days_skip_weekend(self) -> None:
        friday = date(2024, 1, 5)
        monday = date(2024, 1, 8)

        self.assertEqual(business_days_between(friday, monday), 1)
        self.assertEqual(add_business_days(friday, 1), monday)

    def test_parse_transit_days_numeric_range(self) -> None:
        window = parse_transit_days("Standard (3-5 Business Days)")
        self.assertEqual(window, (3, 5))
        single = parse_transit_days("Ships in 4 business days")
        self.assertEqual(single, (4, 4))

    def test_parse_transit_days_empty_returns_none(self) -> None:
        self.assertIsNone(parse_transit_days(None))
        self.assertIsNone(parse_transit_days("   "))

    def test_mapping_fallback_standard_shipping(self) -> None:
        window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 3)
        self.assertEqual(window["max_days"], 5)

    def test_mapping_precedence_longest_key(self) -> None:
        custom_map = {"standard": [3, 5], "standard shipping": [4, 6]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 4)
        self.assertEqual(window["max_days"], 6)

    def test_mapping_invalid_json_falls_back_to_defaults(self) -> None:
        with mock.patch.dict(
            os.environ, {"SHIPPING_METHOD_TRANSIT_MAP_JSON": "{not-valid"}
        ):
            window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 3)
        self.assertEqual(window["max_days"], 5)

    def test_mapping_invalid_json_type_falls_back(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(["standard", [3, 5]])},
        ):
            window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 3)
        self.assertEqual(window["max_days"], 5)

    def test_mapping_invalid_entries_fall_back_when_empty(self) -> None:
        custom_map = {"standard": {"min": 3}, "ground": -1}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 3)
        self.assertEqual(window["max_days"], 5)

    def test_mapping_bool_value_skipped_prefers_specific(self) -> None:
        custom_map = {"standard": True, "standard shipping": [4, 6]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 4)
        self.assertEqual(window["max_days"], 6)

    def test_mapping_string_values_coerce(self) -> None:
        custom_map = {"express": ["1", "2"]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Express Delivery")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 1)
        self.assertEqual(window["max_days"], 2)

    def test_mapping_unicode_digit_strings_ignored(self) -> None:
        custom_map = {"standard": ["²", "³"]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Standard Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 3)
        self.assertEqual(window["max_days"], 5)

    def test_mapping_single_value_list(self) -> None:
        custom_map = {"expedited": [2]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Expedited")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 2)
        self.assertEqual(window["max_days"], 2)

    def test_mapping_tie_breaker_equal_length(self) -> None:
        custom_map = {"ship": [5, 6], "mail": [1, 1]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Ship Mail")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 1)
        self.assertEqual(window["max_days"], 1)

    def test_mapping_prefers_digit_key_when_method_has_digit(self) -> None:
        custom_map = {"2-day": [2, 2], "economy": [5, 7]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("2-day economy shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 2)
        self.assertEqual(window["max_days"], 2)

    def test_mapping_tie_prefers_faster_window(self) -> None:
        custom_map = {"free": [5, 7], "rush": [1, 2]}
        with mock.patch.dict(
            os.environ,
            {"SHIPPING_METHOD_TRANSIT_MAP_JSON": json.dumps(custom_map)},
        ):
            window = normalize_shipping_method("Free Rush Shipping")
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["min_days"], 1)
        self.assertEqual(window["max_days"], 2)

    def test_same_day_order_remaining_window(self) -> None:
        estimate = compute_delivery_estimate(
            order_created_at="2024-01-02",
            shipping_method="Standard Shipping",
            inquiry_date="2024-01-02",
        )
        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate["elapsed_business_days"], 0)
        self.assertEqual(estimate["remaining_min_days"], 3)
        self.assertEqual(estimate["remaining_max_days"], 5)
        self.assertEqual(estimate["eta_human"], "3-5 business days")

    def test_missing_or_invalid_dates_returns_none(self) -> None:
        self.assertIsNone(
            compute_delivery_estimate(None, "Standard Shipping", "2024-01-02")
        )
        self.assertIsNone(
            compute_delivery_estimate("not-a-date", "Standard Shipping", "2024-01-02")
        )
        self.assertIsNone(
            compute_delivery_estimate("2024-01-02", "Standard Shipping", "bad-date")
        )

    def test_standard_shipping_canonical_remaining_window(self) -> None:
        estimate = compute_delivery_estimate(
            order_created_at="2024-01-01",  # Monday
            shipping_method="Standard shipping",
            inquiry_date="2024-01-03",  # Wednesday
        )

        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate["elapsed_business_days"], 2)
        self.assertEqual(estimate["remaining_min_days"], 1)
        self.assertEqual(estimate["remaining_max_days"], 3)
        self.assertEqual(estimate["eta_human"], "1-3 business days")
        self.assertFalse(estimate["is_late"])

    def test_weekend_crossing_remaining_window(self) -> None:
        estimate = compute_delivery_estimate(
            order_created_at="2024-01-05",  # Friday
            shipping_method="Standard (3-5 business days)",
            inquiry_date="2024-01-09",  # Tuesday (crosses weekend)
        )

        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate["elapsed_business_days"], 2)
        self.assertEqual(estimate["remaining_min_days"], 1)
        self.assertEqual(estimate["remaining_max_days"], 3)
        self.assertEqual(estimate["eta_human"], "1-3 business days")
        self.assertFalse(estimate["is_late"])

    def test_remaining_window_allows_zero_minimum(self) -> None:
        estimate = compute_delivery_estimate(
            order_created_at="2024-01-01",
            shipping_method="Standard Shipping (3-5 Business Days)",
            inquiry_date="2024-01-04",
        )

        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate["remaining_min_days"], 0)
        self.assertEqual(estimate["remaining_max_days"], 2)
        self.assertEqual(estimate["eta_human"], "0-2 business days")
        self.assertFalse(estimate["is_late"])

    def test_late_window_reports_any_day_now(self) -> None:
        estimate = compute_delivery_estimate(
            order_created_at="2024-01-01",
            shipping_method="Standard Shipping (3-5 business days)",
            inquiry_date="2024-01-09",
        )

        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertTrue(estimate["is_late"])
        self.assertEqual(estimate["remaining_min_days"], 0)
        self.assertEqual(estimate["remaining_max_days"], 0)
        self.assertEqual(estimate["eta_human"], "should arrive any day now")
        self.assertGreaterEqual(
            estimate["elapsed_business_days"], estimate["window_max_days"]
        )

    def test_shipping_method_normalization_handles_ranges(self) -> None:
        window = normalize_shipping_method("Standard Shipping (5-7 Business Days)")

        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window["bucket"], "Standard")
        self.assertEqual(window["min_days"], 5)
        self.assertEqual(window["max_days"], 7)

        priority = normalize_shipping_method("Priority Overnight")
        self.assertIsNotNone(priority)
        assert priority is not None
        self.assertEqual(priority["bucket"], "Priority")
        self.assertEqual(priority["min_days"], 1)
        self.assertEqual(priority["max_days"], 1)

    def test_preorder_tag_delivery_window_example_matches_requirement(self) -> None:
        estimate = compute_preorder_delivery_estimate(
            order_created_at="2026-02-12",
            shipping_method="Standard Shipping (3-7 business days)",
            inquiry_date="2026-03-14",
            order_tags=["Pre-order"],
        )
        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertIn("March", estimate["preorder_ship_date_human"])
        self.assertIn("29", estimate["preorder_ship_date_human"])
        self.assertIn("2026", estimate["preorder_ship_date_human"])
        self.assertEqual(estimate["delivery_window_human"], "April 1–April 7, 2026")
        self.assertEqual(estimate["ship_days_from_inquiry_human"], "15 days")
        self.assertEqual(estimate["days_from_inquiry_human"], "18–24 days")

    def test_has_preorder_tag_variants(self) -> None:
        self.assertTrue(
            has_preorder_tag(
                None,
                "First Subscription, Pre-order, Recart",
            )
        )
        self.assertTrue(has_preorder_tag(["preorder"]))
        self.assertTrue(has_preorder_tag(["Pre Order"]))
        self.assertFalse(has_preorder_tag(["NotPreorder"]))

    def test_format_helpers(self) -> None:
        self.assertEqual(
            _format_delivery_window(date(2026, 4, 3), date(2026, 4, 3)),
            "April 3, 2026",
        )
        self.assertEqual(
            _format_delivery_window(date(2026, 4, 3), date(2026, 5, 1)),
            "April 3–May 1, 2026",
        )
        self.assertEqual(
            _format_delivery_window(date(2026, 12, 30), date(2027, 1, 2)),
            "December 30, 2026–January 2, 2027",
        )
        self.assertEqual(_format_day_window(3, 3), "3 days")
        self.assertEqual(_format_day_window(3, 5), "3–5 days")

    def test_preorder_delivery_estimate_returns_none_when_invalid(self) -> None:
        self.assertIsNone(
            compute_preorder_delivery_estimate(
                order_created_at="2026-02-01",
                shipping_method="Standard Shipping",
                inquiry_date="2026-02-09",
                order_tags=None,
            )
        )
        self.assertIsNone(
            compute_preorder_delivery_estimate(
                order_created_at="not-a-date",
                shipping_method="Standard Shipping",
                inquiry_date="2026-02-09",
                order_tags=["Pre-order"],
            )
        )
        self.assertIsNone(
            compute_preorder_delivery_estimate(
                order_created_at="2026-02-01",
                shipping_method="Standard Shipping",
                inquiry_date="bad-date",
                order_tags=["Pre-order"],
            )
        )

    def test_preorder_delivery_estimate_omits_negative_days(self) -> None:
        estimate = compute_preorder_delivery_estimate(
            order_created_at="2026-02-01",
            shipping_method="Standard Shipping",
            inquiry_date="2026-04-10",
            order_tags=["Pre-order"],
        )
        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertIsNone(estimate.get("days_from_inquiry_human"))

    def test_no_tracking_reply_non_preorder_regression(self) -> None:
        order_summary = {
            "order_id": "12345",
            "created_at": "2024-01-01",
            "shipping_method": "Standard Shipping",
        }
        reply = build_no_tracking_reply(order_summary, inquiry_date="2024-01-03")
        assert reply is not None
        self.assertEqual(
            reply["body"],
            "Thanks for your patience. Order 12345 was placed on 2024-01-01. "
            "With Standard (3-5 business days) shipping, It should arrive in about "
            "1-3 business days. We'll send tracking as soon as it ships.",
        )

    def test_no_tracking_reply_preorder_includes_ship_and_eta(self) -> None:
        order_summary = {
            "order_id": "PO-2",
            "created_at": "2026-02-12",
            "shipping_method": "Standard Shipping (3-7 business days)",
            "order_tags": ["Pre-order"],
        }
        reply = build_no_tracking_reply(
            order_summary, inquiry_date="2026-03-14", delivery_estimate=None
        )
        assert reply is not None
        self.assertIn("pre-order", reply["body"])
        self.assertIn("scheduled to ship on", reply["body"])
        self.assertIn("in 15 days", reply["body"])
        self.assertIn("April 1–April 7, 2026", reply["body"])
        self.assertIn("in 18–24 days", reply["body"])
        self.assertTrue(reply["body"].endswith("We'll send tracking as soon as it ships."))


class TrackingUrlTests(unittest.TestCase):
    def test_build_tracking_url_variants(self) -> None:
        self.assertEqual(
            build_tracking_url("Fed Ex", "123"),
            "https://www.fedex.com/fedextrack/?trknbr=123",
        )
        self.assertEqual(
            build_tracking_url("Federal Express", "123"),
            "https://www.fedex.com/fedextrack/?trknbr=123",
        )
        self.assertEqual(
            build_tracking_url("United Parcel Service", "1Z999"),
            "https://www.ups.com/track?loc=en_US&tracknum=1Z999",
        )
        self.assertEqual(
            build_tracking_url("United States Postal Service", "9400"),
            "https://tools.usps.com/go/TrackConfirmAction?tLabels=9400",
        )
        self.assertEqual(
            build_tracking_url("DHL Express", "JD014"),
            "https://www.dhl.com/global-en/home/tracking.html?tracking-id=JD014",
        )

    def test_build_tracking_url_unknown_carrier(self) -> None:
        self.assertIsNone(build_tracking_url("Unknown Carrier", "123"))

    def test_build_tracking_url_strips_and_encodes(self) -> None:
        url = build_tracking_url("UPS", " 1Z 999 ")
        self.assertEqual(
            url, "https://www.ups.com/track?loc=en_US&tracknum=1Z%20999"
        )

    def test_build_tracking_reply_preserves_existing_url(self) -> None:
        order_summary = {
            "tracking_number": "ZX999",
            "tracking_url": "https://tracking.example.com/track/ZX999",
            "carrier": "FedEx",
        }
        reply = build_tracking_reply(order_summary)
        assert reply is not None
        self.assertEqual(
            reply["tracking_url"], "https://tracking.example.com/track/ZX999"
        )

    def test_build_tracking_reply_uses_generated_url(self) -> None:
        order_summary = {
            "tracking_number": "ZX999",
            "carrier": "USPS",
        }
        reply = build_tracking_reply(order_summary)
        assert reply is not None
        self.assertEqual(
            reply["tracking_url"],
            "https://tools.usps.com/go/TrackConfirmAction?tLabels=ZX999",
        )


def main() -> int:  # pragma: no cover
    suite = unittest.TestSuite()
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(DeliveryEstimateTests)
    )
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TrackingUrlTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
