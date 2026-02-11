from __future__ import annotations

import json
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

from backend.tests.test_order_lookup_order_id_resolution import (  # noqa: E402
    OrderIdResolutionTests as _OrderIdResolutionTests,
)
from richpanel_middleware.commerce.order_lookup import (  # noqa: E402
    lookup_order_summary,
)
from richpanel_middleware.ingest.envelope import EventEnvelope  # noqa: E402
from richpanel_middleware.integrations.shopify import (  # noqa: E402
    ShopifyClient,
    TransportRequest as ShopifyTransportRequest,
    TransportResponse as ShopifyTransportResponse,
)
from richpanel_middleware.integrations.shipstation import (  # noqa: E402
    ShipStationClient,
    TransportRequest as ShipStationTransportRequest,
    TransportResponse as ShipStationTransportResponse,
)


class _RecordingTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("no response stub provided")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FailingShopifyClient:
    def __init__(self):
        self.called = False

    def get_order(self, *args, **kwargs):
        self.called = True
        raise AssertionError("Shopify should not be invoked when network is disabled")


class _FailingShipStationClient:
    def __init__(self):
        self.called = False

    def list_shipments(self, *args, **kwargs):
        self.called = True
        raise AssertionError(
            "ShipStation should not be invoked when network is disabled"
        )


def _failing_shopify_client() -> _FailingShopifyClient:
    return _FailingShopifyClient()


def _failing_shipstation_client() -> _FailingShipStationClient:
    return _FailingShipStationClient()


def _load_fixture(name: str) -> dict:
    path = ROOT / "scripts" / "fixtures" / "order_lookup" / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _envelope(payload: dict) -> EventEnvelope:
    return EventEnvelope(
        event_id="evt-123",
        received_at="2024-01-01T00:00:00Z",
        group_id="grp-1",
        dedupe_id="dedupe-1",
        payload=payload,
        source="test",
        conversation_id=str(
            payload.get("conversation_id") or payload.get("order_id") or "conv-1"
        ),
    )


class OrderIdResolutionCoverageTests(_OrderIdResolutionTests):
    """Run backend order-id resolution tests under scripts coverage."""


class OrderLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        for key in [
            "SHOPIFY_OUTBOUND_ENABLED",
            "SHIPSTATION_OUTBOUND_ENABLED",
        ]:
            os.environ.pop(key, None)

    def test_offline_lookup_does_not_call_transports(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        envelope = _envelope({"order_id": "A-1", "status": "pending"})

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["order_id"], "A-1")
        self.assertEqual(summary["status"], "pending")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_only_summary_when_network_disabled(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = _load_fixture("payload_order_summary.json")
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "trk_123")
        self.assertEqual(summary["carrier"], "carrier_demo")
        self.assertEqual(summary["shipping_method"], "Priority")
        self.assertEqual(summary["status"], "shipped")
        self.assertEqual(summary["items_count"], 3)
        self.assertEqual(summary["total_price"], "59.99")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_only_summary_skips_network_when_enabled(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = _load_fixture("payload_order_summary.json")
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "trk_123")
        self.assertEqual(summary["carrier"], "carrier_demo")
        self.assertEqual(summary["shipping_method"], "Priority")
        self.assertEqual(summary["status"], "shipped")
        self.assertEqual(summary["items_count"], 3)
        self.assertEqual(summary["total_price"], "59.99")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_missing_shipping_signals_offline_returns_baseline(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        envelope = _envelope({"order_id": "B-1"})

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["order_id"], "B-1")
        self.assertEqual(summary["status"], "unknown")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_tracking_dict_number_is_used_not_stringified(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {"order_id": "T-1", "tracking": {"number": "ABC123"}}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "ABC123")
        self.assertNotIn("{", summary["tracking_number"])
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_tracking_dict_id_fallback(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {"order_id": "T-2", "tracking": {"id": "ABC999"}}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "ABC999")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_orders_list_candidate_is_used(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {
            "orders": [
                {
                    "shipment": {
                        "carrierCode": "orders_carrier",
                        "serviceCode": "orders_ground",
                    },
                    "tracking": {"number": "ORD-123"},
                }
            ]
        }
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "ORD-123")
        self.assertEqual(summary["carrier"], "orders_carrier")
        self.assertEqual(summary["shipping_method"], "orders_ground")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_tracking_url_is_extracted(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {
            "order_id": "T-URL",
            "tracking_number": "1Z999AA10123456784",
            "tracking_url": "https://www.ups.com/track?loc=en_US&tracknum=1Z999AA10123456784",
        }
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(
            summary["tracking_url"],
            "https://www.ups.com/track?loc=en_US&tracknum=1Z999AA10123456784",
        )
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_shipment_dict_used_for_carrier_and_service(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {
            "order_id": "SHIP-1",
            "shipment": {"carrierCode": "ship_demo", "serviceCode": "priority_ship"},
        }
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["carrier"], "ship_demo")
        self.assertEqual(summary["shipping_method"], "priority_ship")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_fulfillments_list_used_for_tracking_and_carrier(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {
            "order_id": "FUL-1",
            "fulfillments": [
                {
                    "tracking_company": "fulfill_carrier",
                    "tracking_numbers": ["FUL-TRACK-1"],
                }
            ],
        }
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "FUL-TRACK-1")
        self.assertEqual(summary["carrier"], "fulfill_carrier")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_nested_order_tracking_string_is_extracted(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {"order": {"tracking": "STR-123"}}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "STR-123")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_nested_order_tracking_numeric_is_extracted(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {"order": {"tracking": 12345}}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["tracking_number"], "12345")
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_shopify_enrichment_merges_fields_when_network_enabled(self) -> None:
        order_payload = _load_fixture("shopify_order.json")
        transport = _RecordingTransport(
            [
                ShopifyTransportResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(order_payload).encode("utf-8"),
                )
            ]
        )
        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )
        shipstation_client = _failing_shipstation_client()

        envelope = _envelope({"order_id": "A-100"})

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=shopify_client,
            shipstation_client=cast(ShipStationClient, shipstation_client),
        )

        self.assertEqual(summary["status"], "fulfilled")
        self.assertEqual(summary["tracking_number"], "1Z999")
        self.assertEqual(summary["carrier"], "UPS")
        self.assertEqual(summary["items_count"], 2)
        self.assertEqual(summary["total_price"], "39.98")
        self.assertEqual(
            summary["line_item_product_ids"],
            ["9733948571895", "9631164694775"],
        )
        self.assertEqual(len(transport.requests), 1)
        request: ShopifyTransportRequest = transport.requests[0]
        self.assertIn("/orders/A-100.json", request.url)
        self.assertFalse(shipstation_client.called)

    def test_shopify_fallback_used_when_payload_has_no_shipping_fields(self) -> None:
        order_payload = _load_fixture("shopify_order.json")
        transport = _RecordingTransport(
            [
                ShopifyTransportResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(order_payload).encode("utf-8"),
                )
            ]
        )
        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )
        shipstation_client = _failing_shipstation_client()

        envelope = _envelope({"order_id": "A-200"})

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=shopify_client,
            shipstation_client=cast(ShipStationClient, shipstation_client),
        )

        self.assertEqual(summary["tracking_number"], "1Z999")
        self.assertEqual(summary["carrier"], "UPS")
        self.assertEqual(summary["status"], "fulfilled")
        self.assertEqual(len(transport.requests), 1)

    def test_shopify_gid_line_item_product_ids_extracted(self) -> None:
        order_payload = _load_fixture("shopify_order_gid.json")
        transport = _RecordingTransport(
            [
                ShopifyTransportResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(order_payload).encode("utf-8"),
                )
            ]
        )
        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )
        shipstation_client = _failing_shipstation_client()
        envelope = _envelope({"order_id": "A-300"})

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=shopify_client,
            shipstation_client=cast(ShipStationClient, shipstation_client),
        )

        self.assertEqual(
            summary["line_item_product_ids"],
            ["9755753185527", "9733948571895"],
        )
        self.assertEqual(len(transport.requests), 1)
        self.assertFalse(shipstation_client.called)

    def test_payload_shipping_opt_in_line_item_product_ids(self) -> None:
        order_payload = _load_fixture("shopify_order.json")
        transport = _RecordingTransport(
            [
                ShopifyTransportResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(order_payload).encode("utf-8"),
                )
            ]
        )
        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )
        shipstation_client = _failing_shipstation_client()
        payload = _load_fixture("payload_order_summary.json")
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            require_line_item_product_ids=True,
            shopify_client=shopify_client,
            shipstation_client=cast(ShipStationClient, shipstation_client),
        )

        self.assertEqual(
            summary["line_item_product_ids"],
            ["9733948571895", "9631164694775"],
        )
        self.assertEqual(len(transport.requests), 1)
        request: ShopifyTransportRequest = transport.requests[0]
        self.assertIn("fields=created_at%2Cid%2Cline_items", request.url)
        self.assertFalse(shipstation_client.called)

    def test_payload_line_item_product_ids_skip_network(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {
            "order_id": "P-100",
            "tracking_number": "TRACK-100",
            "line_items": [{"id": 10, "product_id": 9733948571895}],
        }
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            require_line_item_product_ids=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertEqual(summary["line_item_product_ids"], ["9733948571895"])
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_opt_in_product_ids_fail_closed_on_404(self) -> None:
        transport = _RecordingTransport(
            [
                ShopifyTransportResponse(
                    status_code=404,
                    headers={},
                    body=b"{}",
                )
            ]
        )
        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=transport,
        )
        shipstation_client = _failing_shipstation_client()
        payload = {"order_id": "P-200", "tracking_number": "TRACK-200"}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            require_line_item_product_ids=True,
            shopify_client=shopify_client,
            shipstation_client=cast(ShipStationClient, shipstation_client),
        )

        self.assertNotIn("line_item_product_ids", summary)
        self.assertEqual(len(transport.requests), 1)
        request: ShopifyTransportRequest = transport.requests[0]
        self.assertIn("/orders/P-200.json", request.url)
        self.assertFalse(shipstation_client.called)

    def test_normalize_shopify_product_id_variants(self) -> None:
        from richpanel_middleware.commerce import order_lookup as order_lookup_module

        self.assertIsNone(order_lookup_module._normalize_shopify_product_id(None))
        self.assertIsNone(order_lookup_module._normalize_shopify_product_id(True))
        self.assertEqual(
            order_lookup_module._normalize_shopify_product_id(12345), "12345"
        )
        self.assertEqual(
            order_lookup_module._normalize_shopify_product_id(" 456 "), "456"
        )
        self.assertEqual(
            order_lookup_module._normalize_shopify_product_id(
                "gid://shopify/Product/789"
            ),
            "789",
        )
        self.assertIsNone(
            order_lookup_module._normalize_shopify_product_id(
                "gid://shopify/Product/not-a-number"
            )
        )
        self.assertIsNone(order_lookup_module._normalize_shopify_product_id("abc"))

    def test_extract_shopify_line_item_product_ids_dedup(self) -> None:
        from richpanel_middleware.commerce import order_lookup as order_lookup_module

        payload = {
            "line_items": [
                {"product_id": 9733948571895},
                {"productId": "gid://shopify/Product/9733948571895"},
                {"productId": "gid://shopify/Product/9755753185527"},
                "not-a-dict",
                {"product_id": None},
            ]
        }
        self.assertEqual(
            order_lookup_module._extract_shopify_line_item_product_ids(payload),
            ["9733948571895", "9755753185527"],
        )

    def test_fetch_shopify_line_item_product_ids_dry_run(self) -> None:
        from richpanel_middleware.commerce import order_lookup as order_lookup_module

        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=False,
        )
        product_ids = order_lookup_module._fetch_shopify_line_item_product_ids(
            "P-300",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            client=shopify_client,
        )
        self.assertEqual(product_ids, [])

    def test_fetch_shopify_line_item_product_ids_network_disabled(self) -> None:
        from richpanel_middleware.commerce import order_lookup as order_lookup_module

        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
        )
        product_ids = order_lookup_module._fetch_shopify_line_item_product_ids(
            "P-400",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            client=shopify_client,
        )
        self.assertEqual(product_ids, [])

    def test_payload_opt_in_line_item_product_ids_network_disabled(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {"order_id": "P-500", "tracking_number": "TRACK-500"}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            require_line_item_product_ids=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertNotIn("line_item_product_ids", summary)
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_payload_opt_in_line_item_product_ids_safe_mode(self) -> None:
        shopify = _failing_shopify_client()
        shipstation = _failing_shipstation_client()
        payload = {"order_id": "P-600", "tracking_number": "TRACK-600"}
        envelope = _envelope(payload)

        summary = lookup_order_summary(
            envelope,
            safe_mode=True,
            automation_enabled=True,
            allow_network=True,
            require_line_item_product_ids=True,
            shopify_client=cast(ShopifyClient, shopify),
            shipstation_client=cast(ShipStationClient, shipstation),
        )

        self.assertNotIn("line_item_product_ids", summary)
        self.assertFalse(shopify.called)
        self.assertFalse(shipstation.called)

    def test_shipstation_enrichment_fills_tracking_when_shopify_missing(self) -> None:
        shopify_payload = deepcopy(_load_fixture("shopify_order.json"))
        if isinstance(shopify_payload.get("order"), dict):
            shopify_payload["order"].pop("fulfillments", None)

        shopify_transport = _RecordingTransport(
            [
                ShopifyTransportResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(shopify_payload).encode("utf-8"),
                )
            ]
        )
        shopify_client = ShopifyClient(
            access_token="test-token",
            allow_network=True,
            transport=shopify_transport,
        )

        shipstation_payload = _load_fixture("shipstation_shipments.json")
        shipstation_transport = _RecordingTransport(
            [
                ShipStationTransportResponse(
                    status_code=200,
                    headers={},
                    body=json.dumps(shipstation_payload).encode("utf-8"),
                )
            ]
        )
        shipstation_client = ShipStationClient(
            api_key="key",
            api_secret="secret",
            allow_network=True,
            transport=shipstation_transport,
        )

        envelope = _envelope({"order_id": "A-100"})

        summary = lookup_order_summary(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=shopify_client,
            shipstation_client=shipstation_client,
        )

        self.assertEqual(summary["tracking_number"], "TRACK-123")
        self.assertEqual(summary["carrier"], "fedex")
        self.assertEqual(summary["updated_at"], "2024-01-11T12:00:00Z")
        self.assertEqual(summary["status"], "fulfilled")
        self.assertEqual(len(shipstation_transport.requests), 1)
        request: ShipStationTransportRequest = shipstation_transport.requests[0]
        self.assertIn("orderNumber=A-100", request.url)

        # The fallback should also preserve Shopify-derived pricing + counts.
        self.assertEqual(summary["items_count"], 2)
        self.assertEqual(summary["total_price"], "39.98")


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(OrderIdResolutionCoverageTests))
    suite.addTests(loader.loadTestsFromTestCase(OrderLookupTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
