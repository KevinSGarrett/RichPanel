from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.commerce.order_lookup import (  # noqa: E402
    _extract_order_id,
    lookup_order_summary,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from richpanel_middleware.integrations.shopify import ShopifyClient  # noqa: E402


class OrderIdResolutionTests(unittest.TestCase):
    def test_extract_order_id_missing_returns_unknown(self) -> None:
        payload = {"conversation_id": "conv-123", "id": "conv-123"}
        self.assertEqual(_extract_order_id(payload), "unknown")

    def test_extract_order_id_priority_and_nested(self) -> None:
        payload = {
            "order_id": "id-1",
            "order_number": "num-1",
            "order": {"id": "nested-id", "number": "nested-num"},
        }
        self.assertEqual(_extract_order_id(payload), "id-1")

        payload = {"order_number": "num-2", "order": {"id": "nested-id-2"}}
        self.assertEqual(_extract_order_id(payload), "num-2")

        payload = {"order": {"id": "nested-id-3"}}
        self.assertEqual(_extract_order_id(payload), "nested-id-3")

        payload = {"order": {"number": "nested-num-4"}}
        self.assertEqual(_extract_order_id(payload), "nested-num-4")

    def test_unknown_order_id_skips_shopify_and_logs(self) -> None:
        with mock.patch.object(
            ShopifyClient,
            "get_order",
            side_effect=AssertionError("Shopify should not be called"),
        ) as spy:
            with self.assertLogs(
                "richpanel_middleware.commerce.order_lookup", level="INFO"
            ) as logs:
                summary = lookup_order_summary(
                    build_event_envelope({"conversation_id": "conv-555"}),
                    safe_mode=False,
                    automation_enabled=True,
                    allow_network=True,
                )

        self.assertEqual(summary["order_id"], "unknown")
        self.assertEqual(spy.call_count, 0)
        self.assertIn(
            "Skipping Shopify enrichment (missing order_id)",
            "\n".join(logs.output),
        )
