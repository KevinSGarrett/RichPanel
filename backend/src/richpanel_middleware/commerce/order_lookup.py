from __future__ import annotations

import logging
import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

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

SHOPIFY_ORDER_FIELDS_WITH_CUSTOMER = SHOPIFY_ORDER_FIELDS + [
    "email",
    "customer",
    "order_number",
    "name",
    "id",
]

MAX_EMAIL_ORDER_RESULTS = 50

ORDER_NUMBER_PATTERNS = (
    ("orderNumber_field", re.compile(r"(?mi)\borderNumber\s*:\s*(\d{3,20})\b")),
    ("order_number_text", re.compile(r"(?mi)\border\s*number\s*:\s*(\d{3,20})\b")),
    ("order_no_text", re.compile(r"(?mi)\border\s*no\.?\s*[:#]?\s*(\d{3,20})\b")),
    ("order_number", re.compile(r"(?mi)\border\s*#?\s*(\d{3,20})\b")),
    ("hash_number", re.compile(r"(?<!\d)#(\d{3,10})(?!\d)")),
)

EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


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
        summary = _merge_summary(summary, payload_summary)

    payload_dict = envelope.payload if isinstance(envelope.payload, dict) else {}
    order_id = summary["order_id"]
    resolution: Optional[Dict[str, str]] = None
    shopify_lookup_done = False

    order_number, order_number_source = _extract_order_number_from_payload(payload_dict)
    if order_number and allow_network and not safe_mode and automation_enabled:
        client = shopify_client or ShopifyClient(allow_network=allow_network)
        payload = _lookup_shopify_by_name(
            order_name=order_number,
            allow_network=allow_network,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
            client=client,
        )
        if payload:
            shopify_lookup_done = True
            summary = _merge_summary(summary, _extract_shopify_fields(payload))
            identifier = _extract_shopify_order_identifier(payload) or order_number
            if identifier:
                summary["order_id"] = identifier
                summary["id"] = identifier
                order_id = identifier
            resolution = {
                "resolvedBy": "richpanel_order_number",
                "confidence": "high",
                "reason": "shopify_name_match",
                "order_number_source": order_number_source,
            }

    order_number_name_failed = bool(order_number) and not shopify_lookup_done
    if order_id == "unknown" or order_number_name_failed:
        if allow_network and not safe_mode and automation_enabled:
            email, name = _extract_customer_identity(payload_dict)
            client = shopify_client or ShopifyClient(allow_network=allow_network)
            if not email:
                resolution = {
                    "resolvedBy": "no_match",
                    "confidence": "low",
                    "reason": "no_email_available",
                }
            else:
                orders = _list_shopify_orders_by_email(
                    email=email,
                    allow_network=allow_network,
                    safe_mode=safe_mode,
                    automation_enabled=automation_enabled,
                    client=client,
                )
                payload, identity_resolution = _resolve_orders_by_identity(
                    orders, email=email, name=name
                )
                if payload:
                    shopify_lookup_done = True
                    summary = _merge_summary(summary, _extract_shopify_fields(payload))
                    identifier = _extract_shopify_order_identifier(payload)
                    if identifier:
                        summary["order_id"] = identifier
                        summary["id"] = identifier
                        order_id = identifier
                    if order_number_name_failed:
                        resolution = {
                            "resolvedBy": "richpanel_order_number_then_shopify_identity",
                            "confidence": identity_resolution.get("confidence", "medium"),
                            "reason": "order_number_found_but_name_param_failed_used_email_fallback",
                        }
                    else:
                        resolution = identity_resolution
                else:
                    resolution = identity_resolution
        if order_id == "unknown":
            LOGGER.info(
                "Skipping Shopify enrichment (missing order_id)",
                extra={
                    "has_email": bool(payload_dict.get("email")),
                    "has_name": bool(payload_dict.get("name")),
                },
            )
            if resolution:
                summary["order_resolution"] = resolution
            return summary

    if not _should_enrich(order_id, allow_network, safe_mode, automation_enabled):
        if not allow_network:
            LOGGER.debug(
                "order lookup skipped network: payload missing shipping signals and network disabled"
            )
        return summary

    if not shopify_lookup_done:
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
        if resolution:
            summary["order_resolution"] = resolution
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

    if resolution:
        summary["order_resolution"] = resolution
    return summary


def _should_enrich(
    order_id: str, allow_network: bool, safe_mode: bool, automation_enabled: bool
) -> bool:
    if not order_id or order_id == "unknown":
        return False
    return allow_network and not safe_mode and automation_enabled


def _extract_shopify_order_payload(data: Any) -> Dict[str, Any]:
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
    return payload


def _select_order_from_name_search(order_name: str, data: Any) -> Dict[str, Any]:
    target = str(order_name).strip().lstrip("#")
    orders = data.get("orders") if isinstance(data, dict) else None
    if isinstance(orders, list) and orders:
        for order in orders:
            if not isinstance(order, dict):
                continue
            order_number = order.get("order_number")
            name = order.get("name")
            if order_number is not None and str(order_number).strip() == target:
                return order
            if isinstance(name, str) and name.strip().lstrip("#") == target:
                return order
        if isinstance(orders[0], dict):
            return orders[0]
    if isinstance(orders, list):
        return {}
    return _extract_shopify_order_payload(data)


def _lookup_shopify_by_name(
    *,
    order_name: str,
    allow_network: bool,
    safe_mode: bool,
    automation_enabled: bool,
    client: ShopifyClient,
) -> Dict[str, Any]:
    if not order_name:
        return {}

    normalized = f"#{str(order_name).strip().lstrip('#')}"
    candidates = [normalized]

    for candidate in candidates:
        response = client.find_orders_by_name(
            candidate,
            fields=SHOPIFY_ORDER_FIELDS_WITH_CUSTOMER,
            status="any",
            limit=5,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
            dry_run=not allow_network,
        )
        if response.dry_run:
            continue
        if response.status_code >= 400:
            continue
        payload = _select_order_from_name_search(
            candidate, response.json() or {}
        )
        if payload:
            return payload
    return {}


def _lookup_shopify_by_email_name(
    *,
    email: str,
    name: str,
    allow_network: bool,
    safe_mode: bool,
    automation_enabled: bool,
    client: ShopifyClient,
) -> Dict[str, Any]:
    orders = _list_shopify_orders_by_email(
        email=email,
        allow_network=allow_network,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        client=client,
    )
    payload, _ = _resolve_orders_by_identity(orders, email=email, name=name)
    return payload


def _lookup_shopify_by_email(
    *,
    email: str,
    allow_network: bool,
    safe_mode: bool,
    automation_enabled: bool,
    client: ShopifyClient,
) -> Dict[str, Any]:
    orders = _list_shopify_orders_by_email(
        email=email,
        allow_network=allow_network,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        client=client,
    )
    payload, _ = _resolve_orders_by_identity(orders, email=email, name="")
    return payload


def _resolve_orders_by_identity(
    orders: List[Dict[str, Any]], *, email: str, name: str
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    if not orders:
        return {}, {
            "resolvedBy": "no_match",
            "confidence": "low",
            "reason": "shopify_no_match",
        }
    if name:
        matches = [
            order
            for order in orders
            if _order_matches_name(order, name=name, email=email)
        ]
        if matches:
            return (
                _select_most_recent_order(matches),
                {
                    "resolvedBy": "shopify_email_name",
                    "confidence": "high",
                    "reason": "email_name_match",
                },
            )
    selected = _select_most_recent_order(orders)
    confidence = "high" if len(orders) == 1 else "medium"
    reason = "email_only_single" if len(orders) == 1 else "email_only_multiple"
    return selected, {
        "resolvedBy": "shopify_email_only",
        "confidence": confidence,
        "reason": reason,
    }


def _list_shopify_orders_by_email(
    *,
    email: str,
    allow_network: bool,
    safe_mode: bool,
    automation_enabled: bool,
    client: ShopifyClient,
) -> List[Dict[str, Any]]:
    if not allow_network:
        return []
    response = client.list_orders_by_email(
        email,
        fields=SHOPIFY_ORDER_FIELDS_WITH_CUSTOMER,
        status="any",
        limit=MAX_EMAIL_ORDER_RESULTS,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        dry_run=not allow_network,
    )
    if response.dry_run or response.status_code >= 400:
        return []
    payload = response.json() or {}
    orders = payload.get("orders") if isinstance(payload, dict) else None
    if not isinstance(orders, list):
        return []
    return [order for order in orders if isinstance(order, dict)]


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
    payload: Dict[str, Any] = {}
    if response.status_code == 404:
        payload = _lookup_shopify_by_name(
            order_name=str(order_id).strip(),
            allow_network=allow_network,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
            client=client,
        )
    else:
        payload = _extract_shopify_order_payload(response.json() or {})
    return _extract_shopify_fields(payload)


def _normalize_email(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _normalize_name(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    return " ".join(text.split())


def _extract_customer_identity(payload: Any) -> Tuple[str, str]:
    if not isinstance(payload, dict):
        return "", ""
    customer = payload.get("customer") or payload.get("customer_profile") or {}
    via = payload.get("via") if isinstance(payload.get("via"), dict) else {}
    source = via.get("source") if isinstance(via, dict) else {}
    sender = source.get("from") if isinstance(source, dict) else {}
    email = _normalize_email(
        payload.get("email")
        or payload.get("customer_email")
        or (customer.get("email") if isinstance(customer, dict) else None)
        or (sender.get("address") if isinstance(sender, dict) else None)
    )
    first_name = customer.get("first_name") if isinstance(customer, dict) else None
    last_name = customer.get("last_name") if isinstance(customer, dict) else None
    full_name = (
        payload.get("name")
        or payload.get("customer_name")
        or (customer.get("name") if isinstance(customer, dict) else None)
        or (sender.get("name") if isinstance(sender, dict) else None)
    )
    if not full_name and first_name and last_name:
        full_name = f"{first_name} {last_name}"
    if not email:
        text_candidates: List[str] = []
        for value in (
            payload.get("subject"),
            payload.get("customer_message"),
            payload.get("message"),
            payload.get("body"),
            payload.get("text"),
        ):
            if value:
                text_candidates.append(str(value))
        text_candidates.extend(_iter_comment_texts(payload))
        messages = payload.get("messages") or payload.get("conversation_messages") or []
        if isinstance(messages, list):
            for message in messages:
                if not isinstance(message, dict):
                    continue
                for key in ("plain_body", "body", "text", "message"):
                    value = message.get(key)
                    if value:
                        text_candidates.append(str(value))
        for text in text_candidates:
            match = EMAIL_PATTERN.search(text)
            if match:
                email = _normalize_email(match.group(0))
                break
    return email, _normalize_name(full_name)


def _order_matches_name(order: Dict[str, Any], *, name: str, email: str) -> bool:
    target_name = _normalize_name(name)
    if not target_name:
        return False
    target_email = _normalize_email(email)
    if target_email and _normalize_email(order.get("email")) != target_email:
        customer = order.get("customer")
        customer_email = (
            customer.get("email") if isinstance(customer, dict) else None
        )
        if _normalize_email(customer_email) != target_email:
            return False
    candidates: List[str] = []
    for key in ("customer", "shipping_address", "billing_address"):
        obj = order.get(key)
        if not isinstance(obj, dict):
            continue
        first = _normalize_name(obj.get("first_name"))
        last = _normalize_name(obj.get("last_name"))
        if first and last:
            candidates.append(f"{first} {last}".strip())
            candidates.append(f"{last} {first}".strip())
            candidates.append(first)
            candidates.append(last)
        if obj.get("name"):
            candidates.append(_normalize_name(obj.get("name")))
    candidates = [c for c in candidates if c]
    if target_name in candidates:
        return True
    if " " not in target_name:
        return target_name in set(candidates)
    return False


def _select_most_recent_order(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    def _parse_created_at(order: Dict[str, Any]) -> datetime.datetime:
        raw = order.get("created_at") or order.get("processed_at") or ""
        try:
            return datetime.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return datetime.datetime.min

    return sorted(orders, key=_parse_created_at, reverse=True)[0]


def _extract_shopify_order_identifier(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    order_number = payload.get("order_number")
    if isinstance(order_number, (int, float)) and not isinstance(order_number, bool):
        return str(int(order_number))
    if isinstance(order_number, str) and order_number.strip():
        return order_number.strip()
    name = payload.get("name")
    if isinstance(name, str) and name.strip().startswith("#"):
        return name.strip().lstrip("#")
    order_id = payload.get("id")
    if isinstance(order_id, (int, float)) and not isinstance(order_id, bool):
        return str(int(order_id))
    if isinstance(order_id, str) and order_id.strip():
        return order_id.strip()
    return ""


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
    order_id = _extract_order_id(payload)
    status = (
        _coerce_str(
            payload.get("status")
            or payload.get("fulfillment_status")
            or payload.get("order_status")
        )
        or "unknown"
    )
    carrier = (
        _coerce_str(payload.get("carrier") or payload.get("shipping_carrier")) or ""
    )
    tracking = (
        _coerce_str(payload.get("tracking_number"))
        or _coerce_str(payload.get("trackingNumber"))
        or _coerce_str(payload.get("tracking"))
        or ""
    )
    updated_at = (
        _coerce_str(payload.get("updated_at") or payload.get("fulfillment_updated_at"))
        or envelope.received_at
    )
    items = payload.get("items")
    items_count = _coerce_int(payload.get("items_count") or payload.get("itemsCount"))
    if items_count is None and isinstance(items, list):
        items_count = len(items)
    if items_count is None:
        items_count = 0
    total_price = _coerce_price(
        payload.get("total_price") or payload.get("amount") or payload.get("price")
    )
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
    summary = _merge_summary(
        _extract_shipstation_fields(payload), _extract_shopify_fields(payload)
    )

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
    elif isinstance(tracking_obj, str):
        tracking_number = tracking_number or _coerce_str(tracking_obj)
    elif isinstance(tracking_obj, (int, float)) and not isinstance(tracking_obj, bool):
        tracking_number = tracking_number or _coerce_str(tracking_obj)
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

    tracking_url = summary.get("tracking_url") or _coerce_str(
        payload.get("tracking_url")
        or payload.get("trackingUrl")
        or payload.get("tracking_link")
        or payload.get("status_url")
        or payload.get("statusUrl")
    )
    if isinstance(tracking_obj, dict):
        tracking_url = tracking_url or _coerce_str(
            tracking_obj.get("status_url")
            or tracking_obj.get("statusUrl")
            or tracking_obj.get("tracking_url")
            or tracking_obj.get("trackingUrl")
            or tracking_obj.get("tracking_link")
        )
    if isinstance(shipment_obj, dict):
        tracking_url = tracking_url or _coerce_str(
            shipment_obj.get("tracking_url")
            or shipment_obj.get("trackingUrl")
            or shipment_obj.get("status_url")
            or shipment_obj.get("statusUrl")
            or shipment_obj.get("tracking_link")
        )
    if tracking_url:
        summary["tracking_url"] = tracking_url

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
            payload.get("items_count")
            or payload.get("itemsCount")
            or payload.get("line_items_count")
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
    ):
        value = summary.get(key)
        if value not in (None, "", "unknown"):
            return True
    return False


def _extract_order_id(payload: Dict[str, Any]) -> str:
    for key in ("order_id", "order_number"):
        value = _coerce_str(payload.get(key))
        if value:
            return value

    order = payload.get("order")
    if isinstance(order, dict):
        for key in ("id", "number"):
            value = _coerce_str(order.get(key))
            if value:
                return value

    message_candidates = (
        payload.get("customer_message")
        or payload.get("message")
        or payload.get("body")
        or payload.get("text")
        or payload.get("subject")
    )
    if message_candidates:
        order_number = _extract_order_number_from_text(str(message_candidates))
        if order_number:
            return order_number

    return "unknown"


def _match_order_number_from_text(text: str) -> Tuple[str, str]:
    if not text:
        return "", ""
    normalized = text.replace(",", "")
    for label, pattern in ORDER_NUMBER_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return match.group(1), label
    return "", ""


def _extract_order_number_from_text(text: str) -> str:
    value, _ = _match_order_number_from_text(text)
    return value


def _iter_comment_texts(payload: Dict[str, Any]) -> List[str]:
    ticket_obj = payload.get("ticket") if isinstance(payload.get("ticket"), dict) else payload
    comments = ticket_obj.get("comments") if isinstance(ticket_obj, dict) else []
    if not isinstance(comments, list):
        return []
    texts: List[str] = []
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        text_value = ""
        for key in ("plain_body", "body"):
            value = comment.get(key)
            if value is None:
                continue
            try:
                text_value = str(value).strip()
            except Exception:
                text_value = ""
            if text_value:
                break
        if text_value:
            texts.append(text_value)
    return texts


def _extract_order_number_from_payload(payload: Dict[str, Any]) -> Tuple[str, str]:
    if not isinstance(payload, dict):
        return "", ""

    for key in ("order_number", "orderNumber", "order_no", "orderNo"):
        value = _coerce_str(payload.get(key))
        if value:
            return value.lstrip("#"), "order_number_field"

    order = payload.get("order")
    if isinstance(order, dict):
        for key in ("number", "order_number", "orderNumber", "order_no", "orderNo"):
            value = _coerce_str(order.get(key))
            if value:
                return value.lstrip("#"), "order_number_field"
        name_value = order.get("name")
        if name_value:
            order_number, label = _match_order_number_from_text(str(name_value))
            if order_number:
                return order_number, label

    custom_fields = payload.get("custom_fields")
    if isinstance(custom_fields, dict):
        for key, value in custom_fields.items():
            if "order" not in str(key).lower():
                continue
            order_number = _coerce_str(value)
            if order_number:
                return order_number.lstrip("#"), "order_number_field"
            order_number, label = _match_order_number_from_text(str(value))
            if order_number:
                return order_number, label

    text_sources = [
        payload.get("subject"),
        payload.get("customer_message"),
        payload.get("message"),
        payload.get("body"),
        payload.get("text"),
    ]
    for source in text_sources:
        if not source:
            continue
        order_number, label = _match_order_number_from_text(str(source))
        if order_number:
            return order_number, label

    comment_texts = _iter_comment_texts(payload)
    if comment_texts:
        for label, pattern in ORDER_NUMBER_PATTERNS:
            for text in comment_texts:
                match = pattern.search(text.replace(",", ""))
                if match:
                    return match.group(1), label

    messages = payload.get("messages") or payload.get("conversation_messages") or []
    if isinstance(messages, list):
        message_texts: List[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            for key in ("plain_body", "body", "text", "message"):
                value = message.get(key)
                if value is None:
                    continue
                message_texts.append(str(value))
        if message_texts:
            for label, pattern in ORDER_NUMBER_PATTERNS:
                for text in message_texts:
                    match = pattern.search(text.replace(",", ""))
                    if match:
                        return match.group(1), label

    return "", ""


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
    total_price = _coerce_price(
        payload.get("total_price") or payload.get("current_total_price")
    )

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
    order_number = payload.get("order_number")
    if isinstance(order_number, (int, float)) and not isinstance(order_number, bool):
        summary["order_number"] = str(int(order_number))
    elif isinstance(order_number, str) and order_number.strip():
        summary["order_number"] = order_number.strip().lstrip("#")
    name_value = payload.get("name")
    if isinstance(name_value, str) and name_value.strip().startswith("#"):
        summary.setdefault("order_number", name_value.strip().lstrip("#"))
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
            tracking_candidate = _coerce_str(
                entry.get("trackingNumber") or entry.get("tracking_number")
            )
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
    items_count = (
        len(items)
        if isinstance(items, list)
        else _coerce_int(source.get("items_count"))
    )
    if items_count is None:
        fallback_items = payload.get("items")
        items_count = (
            len(fallback_items)
            if isinstance(fallback_items, list)
            else _coerce_int(payload.get("items_count"))
        )
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
