from __future__ import annotations

import sys
import unittest
from typing import Optional
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(SRC))

from richpanel_middleware.commerce import order_lookup  # noqa: E402
from richpanel_middleware.commerce.order_lookup import (  # noqa: E402
    _extract_customer_identity,
    _extract_order_id,
    _baseline_summary,
    _coerce_int,
    _coerce_price,
    _coerce_str,
    _extract_order_number_from_payload,
    _extract_order_number_from_text,
    _extract_payload_fields,
    _extract_shopify_fields,
    _extract_shopify_order_identifier,
    _extract_shopify_order_payload,
    _extract_shipstation_fields,
    _iter_comment_texts,
    _list_shopify_orders_by_email,
    _lookup_shopify,
    _lookup_shopify_by_email,
    _lookup_shopify_by_email_name,
    _lookup_shopify_by_name,
    _lookup_shipstation,
    _match_order_number_from_text,
    _order_matches_name,
    _resolve_orders_by_identity,
    _select_order_from_name_search,
    _select_most_recent_order,
    _should_enrich,
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

    def test_should_enrich_rejects_missing_order_id(self) -> None:
        self.assertFalse(_should_enrich("", True, False, True))
        self.assertFalse(_should_enrich("unknown", True, False, True))

    def test_extract_shopify_order_payload_variants(self) -> None:
        self.assertEqual(
            _extract_shopify_order_payload({"order": {"id": "o-1"}})["id"],
            "o-1",
        )
        self.assertEqual(
            _extract_shopify_order_payload({"orders": [{"id": "o-2"}]})["id"],
            "o-2",
        )
        self.assertEqual(
            _extract_shopify_order_payload({"id": "o-3"}).get("id"), "o-3"
        )

    def test_select_order_from_name_search_handles_non_dict(self) -> None:
        data = {"orders": ["bad", {"name": "#5555", "order_number": 5555}]}
        selected = _select_order_from_name_search("#5555", data)
        self.assertEqual(selected.get("order_number"), 5555)

    def test_select_order_from_name_search_matches_name_only(self) -> None:
        data = {"orders": [{"name": "#777"}]}
        selected = _select_order_from_name_search("#777", data)
        self.assertEqual(selected.get("name"), "#777")

    def test_select_order_from_name_search_falls_back_to_payload(self) -> None:
        data = {"order": {"id": "o-9"}}
        selected = _select_order_from_name_search("#999", data)
        self.assertEqual(selected.get("id"), "o-9")

    def test_lookup_shopify_by_name_empty_returns_empty(self) -> None:
        class _StubClient:
            def find_orders_by_name(self, *args, **kwargs):
                raise AssertionError("should not be called")

        payload, _ = _lookup_shopify_by_name(
            order_name="",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(),
        )
        self.assertEqual(payload, {})

    def test_lookup_shopify_by_name_handles_exception(self) -> None:
        class _BoomClient:
            def find_orders_by_name(self, *args, **kwargs):
                raise RuntimeError("boom")

        payload, _ = _lookup_shopify_by_name(
            order_name="123",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_BoomClient(),
        )
        self.assertEqual(payload, {})

    def test_lookup_shopify_by_name_diagnostics(self) -> None:
        class _StubResponse:
            def __init__(self, *, status_code: int, payload: dict, headers: dict):
                self.status_code = status_code
                self.dry_run = False
                self._payload = payload
                self.headers = headers
                self.reason = None

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, response):
                self.response = response

            def find_orders_by_name(self, *args, **kwargs):
                return self.response

        payload, diagnostics = _lookup_shopify_by_name(
            order_name="123",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(
                    status_code=401,
                    payload={"orders": []},
                    headers={"x-shopify-request-id": "req-401"},
                )
            ),
        )
        self.assertEqual(payload, {})
        self.assertEqual(diagnostics.get("category"), "auth_fail")
        self.assertEqual(diagnostics.get("request_id"), "req-401")

        payload, diagnostics = _lookup_shopify_by_name(
            order_name="123",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(
                    status_code=429,
                    payload={"orders": []},
                    headers={"x-request-id": "req-429"},
                )
            ),
        )
        self.assertEqual(payload, {})
        self.assertEqual(diagnostics.get("category"), "rate_limited")

        payload, diagnostics = _lookup_shopify_by_name(
            order_name="123",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(
                    status_code=200,
                    payload={"orders": []},
                    headers={"x-request-id": "req-200"},
                )
            ),
        )
        self.assertEqual(payload, {})
        self.assertEqual(diagnostics.get("category"), "no_match")

    def test_resolve_orders_by_identity_no_orders(self) -> None:
        payload, resolution = _resolve_orders_by_identity([], email="x", name="y")
        self.assertEqual(payload, {})
        self.assertEqual(resolution.get("resolvedBy"), "no_match")

    def test_list_shopify_orders_by_email_handles_failures(self) -> None:
        class _StubResponse:
            def __init__(
                self,
                *,
                status_code: int,
                dry_run: bool,
                payload: dict,
                headers: Optional[dict] = None,
                reason: Optional[str] = None,
            ):
                self.status_code = status_code
                self.dry_run = dry_run
                self._payload = payload
                self.headers = headers or {}
                self.reason = reason

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, response):
                self.response = response

            def list_orders_by_email(self, *args, **kwargs):
                return self.response

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=False,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(_StubResponse(status_code=200, dry_run=False, payload={})),
        )
        self.assertEqual(orders, [])
        self.assertIsNone(diagnostics)

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(_StubResponse(status_code=500, dry_run=False, payload={})),
        )
        self.assertEqual(orders, [])
        self.assertEqual(diagnostics.get("category"), "http_error")

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(status_code=200, dry_run=False, payload={"orders": "nope"})
            ),
        )
        self.assertEqual(orders, [])
        self.assertEqual(diagnostics.get("category"), "http_error")

        class _BoomClient:
            def list_orders_by_email(self, *args, **kwargs):
                raise RuntimeError("boom")

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_BoomClient(),
        )
        self.assertEqual(orders, [])
        self.assertEqual(diagnostics.get("category"), "http_error")

    def test_shopify_match_diagnostics_classification(self) -> None:
        class _StubResponse:
            def __init__(self, *, status_code: int, payload: dict, headers: dict):
                self.status_code = status_code
                self.dry_run = False
                self._payload = payload
                self.headers = headers
                self.reason = None

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, response):
                self.response = response

            def list_orders_by_email(self, *args, **kwargs):
                return self.response

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(
                    status_code=401, payload={"orders": []}, headers={"x-request-id": "req-1"}
                )
            ),
        )
        self.assertEqual(orders, [])
        self.assertEqual(diagnostics.get("category"), "auth_fail")
        self.assertEqual(diagnostics.get("status_code"), 401)
        self.assertEqual(diagnostics.get("request_id"), "req-1")

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(
                    status_code=429, payload={"orders": []}, headers={"x-request-id": "req-2"}
                )
            ),
        )
        self.assertEqual(orders, [])
        self.assertEqual(diagnostics.get("category"), "rate_limited")

        orders, diagnostics = _list_shopify_orders_by_email(
            email="x",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient(
                _StubResponse(
                    status_code=200, payload={"orders": []}, headers={"x-request-id": "req-3"}
                )
            ),
        )
        self.assertEqual(orders, [])
        self.assertEqual(diagnostics.get("category"), "no_match")

    def test_lookup_shopify_handles_404_fallback(self) -> None:
        class _StubResponse:
            def __init__(self, *, status_code: int, payload: dict):
                self.status_code = status_code
                self._payload = payload
                self.dry_run = False

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self):
                self.calls = []

            def get_order(self, *args, **kwargs):
                self.calls.append("get_order")
                return _StubResponse(status_code=404, payload={})

            def find_orders_by_name(self, *args, **kwargs):
                self.calls.append("find_orders_by_name")
                return _StubResponse(
                    status_code=200, payload={"orders": [{"order_number": 111}]}
                )

        payload = _lookup_shopify(
            "111",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            client=_StubClient(),
        )
        self.assertEqual(payload.get("order_number"), "111")

    def test_lookup_shopify_skips_when_network_disabled(self) -> None:
        payload = _lookup_shopify(
            "111",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            client=None,
        )
        self.assertEqual(payload, {})

    def test_lookup_shipstation_skips_when_network_disabled(self) -> None:
        summary = _lookup_shipstation(
            "A-1",
            safe_mode=False,
            automation_enabled=True,
            allow_network=False,
            client=None,
        )
        self.assertEqual(summary, {})

    def test_lookup_shopify_by_email_helpers(self) -> None:
        class _StubResponse:
            def __init__(self, payload: dict):
                self.status_code = 200
                self.dry_run = False
                self._payload = payload

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, payload: dict):
                self.payload = payload

            def list_orders_by_email(self, *args, **kwargs):
                return _StubResponse(self.payload)

        client = _StubClient(
            {"orders": [{"order_number": 1, "created_at": "2026-01-01T00:00:00Z"}]}
        )
        payload = _lookup_shopify_by_email_name(
            email="a@example.com",
            name="",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=client,
        )
        self.assertEqual(payload.get("order_number"), 1)
        payload = _lookup_shopify_by_email(
            email="a@example.com",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=client,
        )
        self.assertEqual(payload.get("order_number"), 1)

    def test_lookup_order_summary_identity_resolution_no_orders(self) -> None:
        class _StubResponse:
            status_code = 200
            dry_run = False
            headers = {}
            reason = None

            def json(self):
                return {"orders": []}

        class _StubClient:
            def list_orders_by_email(self, *args, **kwargs):
                return _StubResponse()

        summary = lookup_order_summary(
            build_event_envelope({"email": "nobody@example.com"}),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=_StubClient(),
        )
        resolution = summary.get("order_resolution") or {}
        self.assertEqual(resolution.get("resolvedBy"), "no_match")

    def test_lookup_order_summary_handles_shopify_and_shipstation_errors(self) -> None:
        class _ShopifyClient:
            def __init__(self):
                self.called = False

            def get_order(self, *args, **kwargs):
                self.called = True
                raise RuntimeError("boom")

        class _ShipStationClient:
            def __init__(self):
                self.called = False

            def list_shipments(self, *args, **kwargs):
                self.called = True
                raise RuntimeError("shipstation boom")

        summary = lookup_order_summary(
            build_event_envelope({"order_id": "ERR-1"}),
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            shopify_client=_ShopifyClient(),
            shipstation_client=_ShipStationClient(),
        )
        self.assertEqual(summary["order_id"], "ERR-1")

    def test_extract_order_number_from_payload_paths(self) -> None:
        number, label = _extract_order_number_from_payload(None)
        self.assertEqual((number, label), ("", ""))
        number, label = _extract_order_number_from_payload({"order_number": "123"})
        self.assertEqual((number, label), ("123", "order_number_field"))
        number, label = _extract_order_number_from_payload({"order": {"name": "#123456"}})
        self.assertEqual((number, label), ("123456", "hash_number"))
        number, label = _extract_order_number_from_payload(
            {"custom_fields": {"order_ref": "789"}}
        )
        self.assertEqual((number, label), ("789", "order_number_field"))
        number, label = _extract_order_number_from_payload({"subject": "order #654"})
        self.assertEqual((number, label), ("654", "order_number"))
        number, label = _extract_order_number_from_payload(
            {"comments": [{"plain_body": "order no. 111"}]}
        )
        self.assertEqual((number, label), ("111", "order_no_text"))
        number, label = _extract_order_number_from_payload(
            {"messages": ["bad", {"text": "order #222"}]}
        )
        self.assertEqual((number, label), ("222", "order_number"))

        number, label = _extract_order_number_from_payload(
            {"order": {"order_number": "333"}}
        )
        self.assertEqual((number, label), ("333", "order_number_field"))
        class _FlakyStr:
            def __init__(self) -> None:
                self.calls = 0

            def __str__(self) -> str:
                self.calls += 1
                return "" if self.calls == 1 else "orderNumber: 444"

        number, label = _extract_order_number_from_payload(
            {"custom_fields": {"order_ref": _FlakyStr()}}
        )
        self.assertEqual((number, label), ("444", "orderNumber_field"))

    def test_extract_comment_text_helpers(self) -> None:
        class _BadStr:
            def __str__(self) -> str:
                raise ValueError("boom")

        self.assertEqual(_iter_comment_texts({"comments": "nope"}), [])
        self.assertEqual(
            _iter_comment_texts({"comments": ["bad", {"plain_body": _BadStr()}]}),
            [],
        )

    def test_match_order_number_from_text_empty(self) -> None:
        self.assertEqual(_match_order_number_from_text(""), ("", ""))

    def test_match_order_number_from_text_prefers_order_keyword(self) -> None:
        text = "Order # 1180306 ref #9999999"
        number, label = _match_order_number_from_text(text)
        self.assertEqual(number, "1180306")
        self.assertEqual(label, "order_number")

    def test_match_order_number_from_text_supports_standalone_digits(self) -> None:
        text = "Hi, my order is 654321 and I need tracking."
        number, label = _match_order_number_from_text(text)
        self.assertEqual(number, "654321")
        self.assertEqual(label, "standalone_digits_6_8")

    def test_match_order_number_from_text_skips_date_like_digits(self) -> None:
        text = "Order placed on 20240203 and still no update."
        number, label = _match_order_number_from_text(text)
        self.assertEqual((number, label), ("", ""))

    def test_extract_order_number_from_text_html_anchor_ignored(self) -> None:
        text = '<a href="#m_12345">Click</a>'
        self.assertEqual(_extract_order_number_from_text(text), "")

    def test_extract_order_number_from_text_hash_and_order(self) -> None:
        self.assertEqual(_extract_order_number_from_text("Order # 1180306"), "1180306")
        self.assertEqual(_extract_order_number_from_text("#1180306"), "1180306")

    def test_extract_shopify_fields_and_shipstation_fields(self) -> None:
        self.assertEqual(_extract_shopify_fields("bad"), {})
        payload = {
            "order_number": "777",
            "shipping_lines": [{"title": "Ground"}],
            "line_items": [{"id": 1}],
        }
        summary = _extract_shopify_fields(payload)
        self.assertEqual(summary.get("order_number"), "777")
        self.assertEqual(summary.get("shipping_method"), "Ground")
        self.assertEqual(summary.get("items_count"), 1)

        self.assertEqual(_extract_shipstation_fields("bad"), {})
        summary = _extract_shipstation_fields(
            {
                "shipments": ["bad", {"trackingNumber": "TN1"}],
                "createDate": "2026-01-01T00:00:00Z",
                "orderTotal": "10.50",
            }
        )
        self.assertEqual(summary.get("tracking_number"), "TN1")
        self.assertEqual(summary.get("created_at"), "2026-01-01T00:00:00Z")
        self.assertEqual(summary.get("total_price"), "10.50")

    def test_extract_shopify_fields_prefers_fulfillment_with_tracking(self) -> None:
        payload = {
            "fulfillments": [
                {"tracking_number": "", "tracking_company": "UPS"},
                {"tracking_number": "TN2", "tracking_company": "FedEx"},
            ]
        }
        summary = _extract_shopify_fields(payload)
        self.assertEqual(summary.get("tracking_number"), "TN2")
        self.assertEqual(summary.get("carrier"), "FedEx")

    def test_extract_shopify_fields_falls_back_to_first_fulfillment(self) -> None:
        payload = {"fulfillments": [{"tracking_company": "UPS"}]}
        summary = _extract_shopify_fields(payload)
        self.assertEqual(summary.get("carrier"), "UPS")

    def test_coerce_helpers_handle_exceptions(self) -> None:
        class _BadStr:
            def __str__(self) -> str:
                raise ValueError("boom")

        self.assertIsNone(_coerce_str(_BadStr()))
        self.assertIsNone(_coerce_int("not-int"))
        self.assertEqual(_coerce_price("bad"), "bad")

    def test_extract_customer_identity_non_dict_and_messages(self) -> None:
        self.assertEqual(_extract_customer_identity("nope"), ("", ""))
        payload = {
            "messages": ["bad", {"text": "email: jane@example.com"}],
        }
        email, name = _extract_customer_identity(payload)
        self.assertEqual(email, "jane@example.com")
        self.assertEqual(name, "")

    def test_order_matches_name_with_single_word_and_address(self) -> None:
        order = {"shipping_address": {"name": "Prince"}}
        self.assertTrue(_order_matches_name(order, name="Prince", email=""))

    def test_extract_shopify_order_identifier_extra_cases(self) -> None:
        self.assertEqual(_extract_shopify_order_identifier("bad"), "")
        self.assertEqual(
            _extract_shopify_order_identifier({"order_number": " 999 "}), "999"
        )
        self.assertEqual(
            _extract_shopify_order_identifier({"id": " 123 "}), "123"
        )

    def test_baseline_and_payload_field_counts(self) -> None:
        envelope = build_event_envelope({"items": [{"id": 1}, {"id": 2}]})
        summary = _baseline_summary(envelope)
        self.assertEqual(summary["items_count"], 2)

        payload_summary = _extract_payload_fields(
            {"items": [{"id": 1}], "line_items": [{"id": 2}, {"id": 3}]}
        )
        self.assertEqual(payload_summary.get("items_count"), 2)

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
                self.headers = {}
                self.reason = None

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, responses):
                self.responses = list(responses)

            def find_orders_by_name(self, *args, **kwargs):
                return self.responses.pop(0)

        payload, _ = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=0, dry_run=True, payload={})]),
        )
        self.assertEqual(payload, {})

        payload, _ = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=500, dry_run=False, payload={})]),
        )
        self.assertEqual(payload, {})

        payload, _ = order_lookup._lookup_shopify_by_name(
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
                self.headers = {}
                self.reason = None

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, responses):
                self.responses = list(responses)

            def find_orders_by_name(self, *args, **kwargs):
                return self.responses.pop(0)

        payload, _ = order_lookup._lookup_shopify_by_name(
            order_name="#1057300",
            allow_network=True,
            safe_mode=False,
            automation_enabled=True,
            client=_StubClient([_StubResponse(status_code=404, dry_run=False, payload={})]),
        )
        self.assertEqual(payload, {})
