from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.router import classify_routing  # noqa: E402


class RouterOrderStatusPrecedenceTests(unittest.TestCase):
    def test_order_status_candidate_wins_over_return(self) -> None:
        payload = {
            "message": "I want a return — but also where is my order #1180306?"
        }
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "order_status_tracking")

    def test_return_without_shipping_language_stays_return(self) -> None:
        payload = {"message": "I want a return for order #1180306."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "return_request")

    def test_cancel_order_not_overridden_by_shipment_phrase(self) -> None:
        payload = {"message": "Stop shipment for order #1180306."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "cancel_order")

    def test_shipping_delay_not_shipped_still_matches(self) -> None:
        payload = {"message": "Order #1180306 not shipped yet."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "shipping_delay_not_shipped")

