from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.router import (  # noqa: E402
    classify_routing,
    extract_customer_message,
)


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

    def test_order_status_eta_with_number(self) -> None:
        payload = {"message": "ETA for order #1180306?"}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "order_status_tracking")

    def test_order_status_tracking_without_number(self) -> None:
        payload = {"message": "Where is my package? Tracking update please."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "order_status_tracking")

    def test_delivery_issue_maps_to_order_status_delivery_issue(self) -> None:
        payload = {"message": "Order #1180306 marked delivered but not received."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "order_status_delivery_issue")

    def test_refund_request_not_misclassified(self) -> None:
        payload = {"message": "Refund for order #1180306 please."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "refund_request")

    def test_address_change_not_misclassified(self) -> None:
        payload = {"message": "Change shipping address for order #1180306."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "address_change_order_edit")

    def test_delivered_without_issue_stays_order_status_tracking(self) -> None:
        payload = {"message": "Order #1180306 delivered today."}
        decision = classify_routing(payload)
        self.assertEqual(decision.intent, "order_status_tracking")

    def test_extract_customer_message_from_nested_messages(self) -> None:
        payload = {
            "messages": [
                {"sender_type": "agent", "body": "ignore"},
                {"sender_type": "customer", "body": "Where is my order?"},
            ]
        }
        self.assertEqual(extract_customer_message(payload), "Where is my order?")

    def test_extract_customer_message_from_comments(self) -> None:
        payload = {
            "comments": [
                {"body": "Agent note"},
                {"body": "Tracking update please"},
            ]
        }
        self.assertEqual(extract_customer_message(payload), "Tracking update please")

    def test_extract_customer_message_from_ticket_messages(self) -> None:
        payload = {
            "ticket": {
                "messages": [
                    {"sender_type": "customer", "body": "Need tracking"},
                ]
            }
        }
        self.assertEqual(extract_customer_message(payload), "Need tracking")

    def test_extract_customer_message_from_conversation_messages(self) -> None:
        payload = {
            "conversation_messages": [
                {"sender_type": "customer", "body": "Where is my package?"},
            ]
        }
        self.assertEqual(extract_customer_message(payload), "Where is my package?")

    def test_extract_customer_message_non_dict_returns_default(self) -> None:
        self.assertEqual(extract_customer_message("nope", default="fallback"), "fallback")