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
    business_days_between,
    compute_delivery_estimate,
    normalize_shipping_method,
    parse_transit_days,
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


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DeliveryEstimateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
