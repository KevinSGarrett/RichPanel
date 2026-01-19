from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.delivery_estimate import (  # noqa: E402
    add_business_days,
    business_days_between,
    compute_delivery_estimate,
    normalize_shipping_method,
)


class DeliveryEstimateTests(unittest.TestCase):
    def test_business_days_skip_weekend(self) -> None:
        friday = date(2024, 1, 5)
        monday = date(2024, 1, 8)

        self.assertEqual(business_days_between(friday, monday), 1)
        self.assertEqual(add_business_days(friday, 1), monday)

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
