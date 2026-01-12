from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from richpanel_middleware.ingest.envelope import EventEnvelope
from richpanel_middleware.integrations import ShopifyClient, ShipStationClient

LOGGER = logging.getLogger(__name__)

OrderSummary = Dict[str, Any]

# Fields required for complete order summary extraction including delivery estimates
SHOPIFY_ORDER_FIELDS = [
    "fulfillment_status",
    "financial_status",
    "status",
    "created_at",
    "processed_at",
    "updated_at",
    "current_total_price",
    "total_price",
    "line_items_count",
    "line_items",
    "fulfillments",
    "shipping_lines",
]


def _order_summary_from_payload(payload: Dict[str, Any]) -> Optional[OrderSummary]:
    if not isinstance(payload, dict) or not payload:
        return None

    candidates = []
    seen: set[int] = set()

    def _queue_candidate(obj: Any) -> None:
        if isinstance(obj, dict) and id(obj) not in seen:
            seen.add(id(obj))
            candidates.append(obj)

    _queue_candidate(payload)

    idx = 0
    while idx < len(candidates):
        candidate = candidates[idx]
        _queue_candidate(candidate.get("payload"))
        _queue_candidate(candidate.get("order"))

        orders = candidate.get("orders")
        if isinstance(orders, list) and orders:
            first_order = orders[0]
            if isinstance(first_order, dict):
                _queue_candidate(first_order)

        _queue_candidate(candidate.get("tracking"))
        _queue_candidate(candidate.get("shipment"))

        fulfillments = candidate.get("fulfillments")
        if isinstance(fulfillments, list) and fulfillments:
            first_fulfillment = fulfillments[0]
            if isinstance(first_fulfillment, dict):
                _queue_candidate(first_fulfillment)
        idx += 1

    merged: OrderSummary = {}
    for candidate in candidates:
        merged = _merge_summary(merged, _extract_payload_fields(candidate))

    if _has_payload_shipping_signal(merged):
        return merged
    return None


def lookup_order_summary(
    envelope: EventEnvelope,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool = False,
    shopify_client: Optional[ShopifyClient] = None,
    shipstation_client: Optional[ShipStationClient] = None,
) -> OrderSummary:
    """
    Best-effort order lookup that stays deterministic offline.

    - Uses Shopify + ShipStation clients behind dry-run gates (network disabled by default).
    - Returns a stable OrderSummary dict even when outbound calls are skipped.
    """
    summary = _baseline_summary(envelope)

    payload_summary = _order_summary_from_payload(envelope.payload)
    if payload_summary:
        return _merge_summary(summary, payload_summary)

    order_id = summary["order_id"]

    if not _should_enrich(order_id, allow_network, safe_mode, automation_enabled):
        if not allow_network:
            LOGGER.debug(
                "order lookup skipped network: payload missing shipping signals and network disabled"
            )
        return summary

    try:
        summary = _merge_summary(
            summary,
            _lookup_shopify(
                order_id,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
                client=shopify_client,
            ),
        )
    except Exception:
        # Stay deterministic; fall back to the baseline summary.
        pass

    if summary.get("tracking_number"):
        return summary

    try:
        summary = _merge_summary(
            summary,
            _lookup_shipstation(
                order_id,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
                client=shipstation_client,
            ),
        )
    except Exception:
        pass

    return summary


def _should_enrich(order_id: str, allow_network: bool, safe_mode: bool, automation_enabled: bool) -> bool:
    if not order_id or order_id == "unknown":
        return False
    return allow_network and not safe_mode and automation_enabled


def _lookup_shopify(
    order_id: str,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    client: Optional[ShopifyClient],
) -> OrderSummary:
    if not allow_network:
        return {}

    client = client or ShopifyClient(allow_network=allow_network)
    response = client.get_order(
        order_id,
        fields=SHOPIFY_ORDER_FIELDS,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        dry_run=not allow_network,
    )
    data = response.json() or {}
    payload: Dict[str, Any] = {}
    if isinstance(data, dict):
        if isinstance(data.get("order"), dict):
            payload = data["order"]
        elif isinstance(data.get("orders"), list) and data["orders"]:
            first = data["orders"][0]
            if isinstance(first, dict):
                payload = first
        else:
            payload = data
    return _extract_shopify_fields(payload)


def _lookup_shipstation(
    order_id: str,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    client: Optional[ShipStationClient],
) -> OrderSummary:
    if not allow_network:
        return {}

    client = client or ShipStationClient(allow_network=allow_network)
    response = client.list_shipments(
        params={"orderNumber": str(order_id)},
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        dry_run=not allow_network,
    )
    data = response.json() or {}
    payload = data if isinstance(data, dict) else {}
    return _extract_shipstation_fields(payload)


def _baseline_summary(envelope: EventEnvelope) -> OrderSummary:
    payload = envelope.payload or {}
    order_id = _extract_order_id(payload, envelope.conversation_id)
    status = _coerce_str(
        payload.get("status")
        or payload.get("fulfillment_status")
        or payload.get("order_status")
    ) or "unknown"
    carrier = _coerce_str(payload.get("carrier") or payload.get("shipping_carrier")) or ""
    tracking = (
        _coerce_str(payload.get("tracking_number"))
        or _coerce_str(payload.get("trackingNumber"))
        or _coerce_str(payload.get("tracking"))
        or ""
    )
    updated_at = _coerce_str(payload.get("updated_at") or payload.get("fulfillment_updated_at")) or envelope.received_at
    items = payload.get("items")
    items_count = _coerce_int(payload.get("items_count") or payload.get("itemsCount"))
    if items_count is None and isinstance(items, list):
        items_count = len(items)
    if items_count is None:
        items_count = 0
    total_price = _coerce_price(payload.get("total_price") or payload.get("amount") or payload.get("price"))
    created_at = _coerce_str(
        payload.get("created_at")
        or payload.get("order_created_at")
        or payload.get("ordered_at")
        or payload.get("order_date")
    )
    shipping_method = _coerce_str(
        payload.get("shipping_method")
        or payload.get("shipping_method_name")
        or payload.get("shipping_service")
        or payload.get("shipping_option")
    )

    summary = {
        "order_id": order_id,
        "id": order_id,
        "status": status,
        "carrier": carrier,
        "tracking_number": tracking,
        "updated_at": updated_at,
        "items_count": items_count,
        "total_price": total_price,
    }
    if created_at:
        summary["created_at"] = created_at
    if shipping_method:
        summary["shipping_method"] = shipping_method
        summary["shipping_method_name"] = shipping_method
    return summary


def _extract_payload_fields(payload: Dict[str, Any]) -> OrderSummary:
    if not isinstance(payload, dict):
        return {}

    # Start with shapes that mirror Shopify and ShipStation responses.
    summary = _merge_summary(_extract_shipstation_fields(payload), _extract_shopify_fields(payload))

    status = summary.get("status") or _coerce_str(
        payload.get("fulfillment_status")
        or payload.get("order_status")
        or payload.get("status")
        or payload.get("financial_status")
        or payload.get("fulfillmentStatus")
        or payload.get("orderStatus")
        or payload.get("financialStatus")
    )
    if status:
        summary["status"] = status

    tracking_obj = payload.get("tracking")
    tracking_number = summary.get("tracking_number") or _first_str(
        payload.get("tracking_numbers") or payload.get("trackingNumbers")
    )
    if isinstance(tracking_obj, dict):
        tracking_number = tracking_number or _coerce_str(
            tracking_obj.get("number")
            or tracking_obj.get("id")
            or tracking_obj.get("trackingNumber")
            or tracking_obj.get("tracking_number")
        )
    tracking_number = tracking_number or _coerce_str(
        payload.get("tracking_number")
        or payload.get("trackingNumber")
        or payload.get("tracking_number_id")
    )
    if tracking_number:
        summary["tracking_number"] = tracking_number

    carrier = summary.get("carrier") or _coerce_str(
        payload.get("carrier")
        or payload.get("carrierCode")
        or payload.get("shipping_carrier")
        or payload.get("tracking_company")
        or payload.get("shipping_company")
        or payload.get("shippingCarrier")
        or payload.get("carrier_code")
    )
    if isinstance(tracking_obj, dict):
        carrier = carrier or _coerce_str(
            tracking_obj.get("carrier")
            or tracking_obj.get("carrierCode")
            or tracking_obj.get("shippingCarrier")
            or tracking_obj.get("company")
        )

    shipment_obj = payload.get("shipment")
    if isinstance(shipment_obj, dict):
        carrier = carrier or _coerce_str(
            shipment_obj.get("carrier")
            or shipment_obj.get("carrierCode")
            or shipment_obj.get("shippingCarrier")
        )

    if carrier:
        summary["carrier"] = carrier

    shipping_method = summary.get("shipping_method") or _coerce_str(
        payload.get("shipping_method")
        or payload.get("shipping_method_name")
        or payload.get("shipping_service")
        or payload.get("shipping_option")
        or payload.get("serviceCode")
        or payload.get("service_name")
        or payload.get("shippingMethod")
        or payload.get("shippingService")
    )
    if isinstance(tracking_obj, dict):
        shipping_method = shipping_method or _coerce_str(
            tracking_obj.get("service")
            or tracking_obj.get("shipping_method")
            or tracking_obj.get("shippingMethod")
        )
    if isinstance(shipment_obj, dict):
        shipping_method = shipping_method or _coerce_str(
            shipment_obj.get("serviceCode")
            or shipment_obj.get("service")
            or shipment_obj.get("shippingMethod")
        )
    if shipping_method:
        summary["shipping_method"] = shipping_method
        summary["shipping_method_name"] = shipping_method

    updated_at = summary.get("updated_at") or _coerce_str(
        payload.get("updated_at")
        or payload.get("fulfillment_updated_at")
        or payload.get("processed_at")
        or payload.get("updatedAt")
        or payload.get("processedAt")
    )
    if updated_at:
        summary["updated_at"] = updated_at

    created_at = summary.get("created_at") or _coerce_str(
        payload.get("created_at")
        or payload.get("order_created_at")
        or payload.get("ordered_at")
        or payload.get("order_date")
    )
    if created_at:
        summary["created_at"] = created_at

    items_count = summary.get("items_count")
    if items_count is None:
        items_count = _coerce_int(
            payload.get("items_count") or payload.get("itemsCount") or payload.get("line_items_count")
        )
        if items_count is None:
            items = payload.get("items")
            if isinstance(items, list):
                items_count = len(items)
            else:
                line_items = payload.get("line_items")
                if isinstance(line_items, list):
                    items_count = len(line_items)
    if items_count is not None:
        summary["items_count"] = items_count

    total_price = summary.get("total_price") or _coerce_price(
        payload.get("total_price")
        or payload.get("current_total_price")
        or payload.get("amount")
        or payload.get("price")
    )
    if total_price is not None:
        summary["total_price"] = total_price

    return summary


def _has_payload_shipping_signal(summary: OrderSummary) -> bool:
    if not summary:
        return False

    for key in (
        "tracking_number",
        "carrier",
        "shipping_method",
        "status",
    ):
        value = summary.get(key)
        if value not in (None, "", "unknown"):
            return True
    return False


def _extract_order_id(payload: Dict[str, Any], conversation_id: str) -> str:
    for key in ("order_id", "orderId", "order_number", "orderNumber", "id"):
        value = _coerce_str(payload.get(key))
        if value:
            return value
    return conversation_id or "unknown"


def _extract_shopify_fields(payload: Dict[str, Any]) -> OrderSummary:
    if not isinstance(payload, dict):
        return {}

    status = _coerce_str(
        payload.get("fulfillment_status")
        or payload.get("financial_status")
        or payload.get("status")
    )
    created_at = _coerce_str(payload.get("created_at") or payload.get("processed_at"))
    updated_at = _coerce_str(payload.get("updated_at"))
    total_price = _coerce_price(payload.get("total_price") or payload.get("current_total_price"))

    tracking_number = ""
    carrier = ""
    fulfillments = payload.get("fulfillments")
    if isinstance(fulfillments, list) and fulfillments:
        first = fulfillments[0]
        if isinstance(first, dict):
            carrier = _coerce_str(first.get("tracking_company")) or carrier
            tracking_number = (
                _first_str(first.get("tracking_numbers"))
                or _coerce_str(first.get("tracking_number"))
                or tracking_number
            )
    shipping_method = None
    shipping_lines = payload.get("shipping_lines")
    if isinstance(shipping_lines, list) and shipping_lines:
        first_line = shipping_lines[0]
        if isinstance(first_line, dict):
            shipping_method = _coerce_str(
                first_line.get("title")
                or first_line.get("code")
                or first_line.get("delivery_category")
            )
    shipping_method = shipping_method or _coerce_str(payload.get("shipping_line"))

    line_items = payload.get("line_items")
    items_count = _coerce_int(payload.get("line_items_count"))
    if items_count is None and isinstance(line_items, list):
        items_count = len(line_items)

    summary: OrderSummary = {}
    if status:
        summary["status"] = status
    if created_at:
        summary["created_at"] = created_at
    if updated_at:
        summary["updated_at"] = updated_at
    if carrier:
        summary["carrier"] = carrier
    if tracking_number:
        summary["tracking_number"] = tracking_number
    if items_count is not None:
        summary["items_count"] = items_count
    if total_price is not None:
        summary["total_price"] = total_price
    if shipping_method:
        summary["shipping_method"] = shipping_method
        summary["shipping_method_name"] = shipping_method
    return summary


def _extract_shipstation_fields(payload: Dict[str, Any]) -> OrderSummary:
    if not isinstance(payload, dict):
        return {}

    shipments = payload.get("shipments")
    shipment_payload: Optional[Dict[str, Any]] = None
    if isinstance(shipments, list) and shipments:
        for entry in shipments:
            if not isinstance(entry, dict):
                continue
            shipment_payload = entry
            tracking_candidate = _coerce_str(entry.get("trackingNumber") or entry.get("tracking_number"))
            if tracking_candidate:
                break

    source = shipment_payload or payload

    status = _coerce_str(
        source.get("orderStatus")
        or source.get("orderStatusName")
        or source.get("status")
        or payload.get("orderStatus")
        or payload.get("orderStatusName")
        or payload.get("status")
    )
    tracking = _coerce_str(
        source.get("trackingNumber")
        or source.get("tracking_number")
        or payload.get("trackingNumber")
        or payload.get("tracking_number")
    )
    carrier = _coerce_str(
        source.get("carrierCode")
        or source.get("serviceCode")
        or source.get("carrier")
        or payload.get("carrierCode")
        or payload.get("serviceCode")
        or payload.get("carrier")
    )
    shipping_method = _coerce_str(
        source.get("serviceCode")
        or payload.get("serviceCode")
        or payload.get("service_name")
    )
    updated_at = _coerce_str(
        source.get("shipDate")
        or source.get("createDate")
        or source.get("modifyDate")
        or source.get("updateDate")
        or source.get("modifiedAt")
        or payload.get("modifiedAt")
        or payload.get("updateDate")
    )
    created_at = _coerce_str(
        source.get("createDate")
        or payload.get("createDate")
        or payload.get("orderDate")
    )
    items = source.get("items")
    items_count = len(items) if isinstance(items, list) else _coerce_int(source.get("items_count"))
    if items_count is None:
        fallback_items = payload.get("items")
        items_count = len(fallback_items) if isinstance(fallback_items, list) else _coerce_int(payload.get("items_count"))
    total_price = _coerce_price(
        source.get("orderTotal")
        or source.get("amountPaid")
        or source.get("shipmentCost")
        or payload.get("orderTotal")
        or payload.get("amountPaid")
    )

    summary: OrderSummary = {}
    if status:
        summary["status"] = status
    if tracking:
        summary["tracking_number"] = tracking
    if carrier:
        summary["carrier"] = carrier
    if shipping_method:
        summary["shipping_method"] = shipping_method
        summary["shipping_method_name"] = shipping_method
    if updated_at:
        summary["updated_at"] = updated_at
    if created_at:
        summary["created_at"] = created_at
    if items_count is not None:
        summary["items_count"] = items_count
    if total_price is not None:
        summary["total_price"] = total_price
    return summary


def _merge_summary(base: OrderSummary, updates: OrderSummary) -> OrderSummary:
    merged = dict(base)
    for key, value in updates.items():
        if value is not None:
            merged[key] = value
    return merged


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return None


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _coerce_price(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        number = float(str(value))
        return f"{number:.2f}"
    except Exception:
        return _coerce_str(value)


def _first_str(values: Any) -> Optional[str]:
    if isinstance(values, list) and values:
        return _coerce_str(values[0])
    return _coerce_str(values)

