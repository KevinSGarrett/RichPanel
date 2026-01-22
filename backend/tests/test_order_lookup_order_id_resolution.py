from __future__ import annotations

import sys
from pathlib import Path

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


def test_extract_order_id_missing_returns_unknown() -> None:
    payload = {"conversation_id": "conv-123", "id": "conv-123"}
    assert _extract_order_id(payload, "conv-123") == "unknown"


def test_allow_network_does_not_call_shopify_when_order_id_unknown(
    monkeypatch,
) -> None:
    calls = {"count": 0}

    def _spy_get_order(self, *args, **kwargs):
        calls["count"] += 1
        raise AssertionError(
            "Shopify should not be called when order_id is unknown"
        )

    monkeypatch.setattr(ShopifyClient, "get_order", _spy_get_order)
    envelope = build_event_envelope({"conversation_id": "conv-555"})

    summary = lookup_order_summary(
        envelope,
        safe_mode=False,
        automation_enabled=True,
        allow_network=True,
    )

    assert summary["order_id"] == "unknown"
    assert calls["count"] == 0
