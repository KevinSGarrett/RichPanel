from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(SRC))

from richpanel_middleware.commerce.order_lookup import (  # noqa: E402
    _extract_order_id,
    lookup_order_summary,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from richpanel_middleware.integrations.shopify import ShopifyClient  # noqa: E402


def test_extract_order_id_missing_returns_unknown() -> None:
    payload = {"conversation_id": "conv-123", "id": "conv-123"}
    assert _extract_order_id(payload, "conv-123") == "unknown"

def test_extract_order_id_reads_nested_order_fields() -> None:
    payload = {"order": {"id": "order-1"}}
    assert _extract_order_id(payload, "conv-1") == "order-1"

    payload = {"order": {"number": "order-2"}}
    assert _extract_order_id(payload, "conv-1") == "order-2"


def test_unknown_order_id_skips_shopify_and_logs(
    monkeypatch,
    caplog,
) -> None:
    spy = mock.Mock(side_effect=AssertionError("Shopify should not be called"))
    monkeypatch.setattr(ShopifyClient, "get_order", spy)
    envelope = build_event_envelope({"conversation_id": "conv-555"})

    with caplog.at_level(logging.INFO):
        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
        )

    assert summary["order_id"] == "unknown"
    assert spy.call_count == 0
    assert "Skipping Shopify enrichment (missing order_id)" in caplog.text
