from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(SRC))

from richpanel_middleware.commerce import order_lookup  # noqa: E402
from richpanel_middleware.commerce.order_lookup import (  # noqa: E402
    _extract_order_id,
    lookup_order_summary,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # noqa: E402
from richpanel_middleware.integrations.shopify import (  # noqa: E402
    ShopifyClient,
    TransportResponse,
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

    def test_order_number_falls_back_to_name_search(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=404, headers={}, body=b'{"errors":"Not Found"}'
                ),
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=(
                        b'{"orders":[{"created_at":"2026-01-24T00:00:00Z",'
                        b'"shipping_lines":[{"title":"USPS/UPS Ground"}],'
                        b'"fulfillments":[{"tracking_number":"TN123","tracking_company":"UPS"}],'
                        b'"total_price":"10.00"}]}'
                    ),
                ),
            ]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        summary = lookup_order_summary(
            build_event_envelope({"order_number": "1057300"}),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        self.assertEqual(summary["order_id"], "1057300")
        self.assertEqual(summary["shipping_method"], "USPS/UPS Ground")
        self.assertEqual(summary["tracking_number"], "TN123")
        self.assertEqual(len(transport.requests), 2)
        self.assertIn("/orders/1057300.json", transport.requests[0].url)
        self.assertIn("orders.json", transport.requests[1].url)
        self.assertIn("name=%231057300", transport.requests[1].url)

    def test_lookup_shopify_by_name_skips_dry_run_and_errors(self) -> None:
        class _StubResponse:
            def __init__(self, *, status_code: int, dry_run: bool, payload: dict):
                self.status_code = status_code
                self.dry_run = dry_run
                self._payload = payload

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, responses):
                self.responses = list(responses)

            def find_order_by_name(self, *args, **kwargs):
                return self.responses.pop(0)

        payload = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=0, dry_run=True, payload={})]),
        )
        self.assertEqual(payload, {})

        payload = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=500, dry_run=False, payload={})]),
        )
        self.assertEqual(payload, {})

        payload = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                [
                    _StubResponse(
                        status_code=200,
                        dry_run=False,
                        payload={"orders": [{"shipping_lines": [{"title": "Standard"}]}]},
                    )
                ]
            ),
        )
        self.assertEqual(payload.get("shipping_lines")[0]["title"], "Standard")

    def test_lookup_shopify_by_name_handles_hash_prefixed(self) -> None:
        class _StubResponse:
            def __init__(self, *, status_code: int, dry_run: bool, payload: dict):
                self.status_code = status_code
                self.dry_run = dry_run
                self._payload = payload

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, responses):
                self.responses = list(responses)

            def find_order_by_name(self, *args, **kwargs):
                return self.responses.pop(0)

        payload = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=404, dry_run=False, payload={})]),
        )
        self.assertEqual(payload, {})
