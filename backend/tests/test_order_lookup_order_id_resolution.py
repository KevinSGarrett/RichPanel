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
    _extract_customer_identity,
    _extract_order_id,
    _extract_shopify_order_identifier,
    _order_matches_name,
    _select_most_recent_order,
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

        payload = {"customer_message": "orderNumber: 1121654"}
        self.assertEqual(_extract_order_id(payload), "1121654")

    def test_extract_customer_identity_from_payload_text(self) -> None:
        payload = {
            "subject": "Order update for alice@example.com",
            "customer_profile": {"first_name": "Alice", "last_name": "Smith"},
        }
        email, name = _extract_customer_identity(payload)
        self.assertEqual(email, "alice@example.com")
        self.assertEqual(name, "alice smith")

        payload = {
            "comments": [
                {"plain_body": "contact bob@example.com for updates"}
            ],
            "messages": [{"text": "also cc carol@example.com"}],
        }
        email, name = _extract_customer_identity(payload)
        self.assertEqual(email, "bob@example.com")
        self.assertEqual(name, "")

    def test_order_matches_name_and_email(self) -> None:
        order = {
            "email": "jane@example.com",
            "customer": {"first_name": "Jane", "last_name": "Doe"},
        }
        self.assertTrue(
            _order_matches_name(order, name="Jane Doe", email="jane@example.com")
        )
        self.assertFalse(
            _order_matches_name(order, name="Jane Doe", email="nope@example.com")
        )
        self.assertFalse(_order_matches_name(order, name="", email="jane@example.com"))

    def test_select_most_recent_order_handles_bad_dates(self) -> None:
        recent = {"created_at": "2026-01-10T00:00:00Z", "order_number": 2}
        invalid = {"created_at": "not-a-date", "order_number": 1}
        self.assertEqual(_select_most_recent_order([invalid, recent]), recent)

    def test_extract_shopify_order_identifier_variants(self) -> None:
        self.assertEqual(
            _extract_shopify_order_identifier({"order_number": 123456}), "123456"
        )
        self.assertEqual(
            _extract_shopify_order_identifier({"name": "#112233"}), "112233"
        )
        self.assertEqual(
            _extract_shopify_order_identifier({"id": 987654321}), "987654321"
        )
        self.assertEqual(
            _extract_shopify_order_identifier({"id": "ABC123"}), "ABC123"
        )

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
        resolution = summary.get("order_resolution") or {}
        self.assertEqual(resolution.get("resolvedBy"), "no_match")
        self.assertEqual(resolution.get("confidence"), "low")
        self.assertEqual(resolution.get("reason"), "no_email_available")
        self.assertEqual(spy.call_count, 0)
        self.assertIn(
            "Skipping Shopify enrichment (missing order_id)",
            "\n".join(logs.output),
        )

    def test_order_number_comment_uses_name_search(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=(
                        b'{"orders":[{"created_at":"2026-01-24T00:00:00Z",'
                        b'"order_number":1057300,'
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
            build_event_envelope(
                {"comments": [{"plain_body": "orderNumber: 1057300"}]}
            ),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        self.assertEqual(summary["order_id"], "1057300")
        self.assertEqual(summary["shipping_method"], "USPS/UPS Ground")
        self.assertEqual(summary["tracking_number"], "TN123")
        resolution = summary.get("order_resolution") or {}
        self.assertEqual(resolution.get("resolvedBy"), "richpanel_order_number")
        self.assertEqual(resolution.get("confidence"), "high")
        self.assertEqual(resolution.get("reason"), "shopify_name_match")
        self.assertEqual(resolution.get("order_number_source"), "orderNumber_field")
        self.assertEqual(len(transport.requests), 1)
        self.assertIn("orders.json", transport.requests[0].url)
        self.assertIn("name=%231057300", transport.requests[0].url)
        self.assertIn("limit=5", transport.requests[0].url)

    def test_order_number_name_search_uses_hash_prefix(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=b'{"orders":[{"order_number":1121654}]}',
                )
            ]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        summary = lookup_order_summary(
            build_event_envelope(
                {"comments": [{"plain_body": "orderNumber: 1121654"}]}
            ),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        self.assertEqual(summary["order_id"], "1121654")
        self.assertIn("name=%231121654", transport.requests[0].url)

    def test_hash_order_number_uses_name_search(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=(
                        b'{"orders":[{"created_at":"2026-01-24T00:00:00Z",'
                        b'"order_number":1140757,"name":"#1140757"}]}'
                    ),
                )
            ]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        summary = lookup_order_summary(
            build_event_envelope({"comments": [{"body": "#1140757"}]}),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        self.assertEqual(summary["order_id"], "1140757")
        resolution = summary.get("order_resolution") or {}
        self.assertEqual(resolution.get("resolvedBy"), "richpanel_order_number")
        self.assertEqual(resolution.get("confidence"), "high")
        self.assertEqual(resolution.get("reason"), "shopify_name_match")
        self.assertEqual(resolution.get("order_number_source"), "hash_number")
        self.assertIn("name=%231140757", transport.requests[0].url)

    def test_order_number_name_search_falls_back_to_identity(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200, headers={}, body=b'{"orders":[]}'
                ),
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=(
                        b'{"orders":[{"order_number":1188605,'
                        b'"created_at":"2026-01-24T00:00:00Z",'
                        b'"email":"jane@example.com",'
                        b'"customer":{"first_name":"Jane","last_name":"Doe"}}]}'
                    ),
                ),
            ]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        summary = lookup_order_summary(
            build_event_envelope(
                {
                    "comments": [{"plain_body": "orderNumber: 1188605"}],
                    "email": "jane@example.com",
                    "name": "Jane Doe",
                }
            ),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        resolution = summary.get("order_resolution") or {}
        self.assertEqual(
            resolution.get("resolvedBy"),
            "richpanel_order_number_then_shopify_identity",
        )
        self.assertEqual(resolution.get("confidence"), "high")
        self.assertEqual(
            resolution.get("reason"),
            "order_number_found_but_name_param_failed_used_email_fallback",
        )
        self.assertEqual(len(transport.requests), 2)
        self.assertIn("name=%231188605", transport.requests[0].url)
        self.assertIn("email=jane%40example.com", transport.requests[1].url)

    def test_missing_order_id_falls_back_to_email_name(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=(
                        b'{"orders":[{"order_number":1121654,'
                        b'"created_at":"2026-01-20T00:00:00Z",'
                        b'"email":"jane@example.com",'
                        b'"customer":{"first_name":"Jane","last_name":"Doe"},'
                        b'"shipping_lines":[{"title":"Ground"}],'
                        b'"fulfillments":[{"tracking_number":"TN123"}]},'
                        b'{"order_number":5555555,'
                        b'"created_at":"2026-01-21T00:00:00Z",'
                        b'"email":"jane@example.com",'
                        b'"customer":{"first_name":"Bob","last_name":"Smith"}}]}'
                    ),
                )
            ]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        summary = lookup_order_summary(
            build_event_envelope(
                {"email": "jane@example.com", "name": "Jane Doe"}
            ),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        self.assertEqual(summary["order_id"], "1121654")
        self.assertEqual(summary["shipping_method"], "Ground")
        self.assertEqual(summary["tracking_number"], "TN123")
        resolution = summary.get("order_resolution") or {}
        self.assertEqual(resolution.get("resolvedBy"), "shopify_email_name")
        self.assertEqual(resolution.get("confidence"), "high")
        self.assertEqual(resolution.get("reason"), "email_name_match")
        self.assertEqual(len(transport.requests), 1)
        self.assertIn("orders.json", transport.requests[0].url)
        self.assertIn("email=jane%40example.com", transport.requests[0].url)

    def test_missing_order_id_falls_back_to_email_only(self) -> None:
        transport = _RecordingTransport(
            [
                TransportResponse(
                    status_code=200,
                    headers={},
                    body=(
                        b'{"orders":[{"order_number":1111111,'
                        b'"created_at":"2026-01-01T00:00:00Z",'
                        b'"email":"solo@example.com"},'
                        b'{"order_number":2222222,'
                        b'"created_at":"2026-01-10T00:00:00Z",'
                        b'"email":"solo@example.com"}]}'
                    ),
                )
            ]
        )
        client = ShopifyClient(
            access_token="test-token", allow_network=True, transport=transport
        )

        summary = lookup_order_summary(
            build_event_envelope({"email": "solo@example.com"}),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=client,
        )

        self.assertEqual(summary["order_id"], "2222222")
        resolution = summary.get("order_resolution") or {}
        self.assertEqual(resolution.get("resolvedBy"), "shopify_email_only")
        self.assertEqual(resolution.get("confidence"), "medium")
        self.assertEqual(resolution.get("reason"), "email_only_multiple")
        self.assertEqual(len(transport.requests), 1)

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

            def find_orders_by_name(self, *args, **kwargs):
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

            def find_orders_by_name(self, *args, **kwargs):
                return self.responses.pop(0)

        payload = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=404, dry_run=False, payload={})]),
        )
        self.assertEqual(payload, {})
