from __future__ import annotations

import json
import logging
import os
import re
from urllib.parse import quote
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

DEFAULT_SHIPPING_METHOD_TRANSIT_MAP: Dict[str, tuple[int, int]] = {
    "priority": (1, 1),
    "overnight": (1, 1),
    "next day": (1, 1),
    "next-day": (1, 1),
    "1-day": (1, 1),
    "1 day": (1, 1),
    "express": (1, 2),
    "expedited": (2, 3),
    "rush": (1, 2),
    "rushed": (1, 2),
    "2-day": (2, 2),
    "2 day": (2, 2),
    "two day": (2, 2),
    "standard": (3, 5),
    "ground": (3, 7),
    "economy": (5, 7),
    "free": (5, 7),
    "postal": (5, 7),
    "mail": (5, 7),
}


def _coerce_date(value: Any) -> date:
    """Convert a datetime/date/ISO string into a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty date string")

        normalized = text.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            pass

        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            pass

    raise ValueError(f"unsupported date value: {value!r}")


def business_days_between(a: Any, b: Any) -> int:
    """Count business days between two dates (excludes the start date)."""
    start = _coerce_date(a)
    end = _coerce_date(b)
    if start == end:
        return 0

    sign = 1
    if start > end:
        start, end = end, start
        sign = -1

    days = 0
    cursor = start
    while cursor < end:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            days += 1
    return days * sign


def add_business_days(value: Any, days: int) -> date:
    """Move forward/backward by N business days from a given date."""
    current = _coerce_date(value)
    if days == 0:
        return current

    remaining = abs(days)
    step = 1 if days > 0 else -1
    while remaining > 0:
        current += timedelta(days=step)
        if current.weekday() < 5:
            remaining -= 1
    return current


def _parse_numeric_window(text: str) -> Optional[tuple[int, int]]:
    range_match = re.search(r"(\d+)\s*(?:-|\u2013|to)\s*(\d+)", text)
    if range_match:
        first, second = int(range_match.group(1)), int(range_match.group(2))
        return (first, second) if first <= second else (second, first)

    single_match = re.search(r"(\d+)\s*(?:business\s+days?|bd|days?)", text)
    if single_match:
        number = int(single_match.group(1))
        return number, number

    return None


def parse_transit_days(raw: Optional[str]) -> Optional[tuple[int, int]]:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None
    return _parse_numeric_window(text)


def _coerce_transit_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdecimal() and text.isascii():
            try:
                return int(text)
            except ValueError:
                return None
        return None
    return None


def _normalize_transit_window(value: Any) -> Optional[tuple[int, int]]:
    if isinstance(value, (list, tuple)):
        if len(value) not in (1, 2):
            return None
        numbers = []
        for item in value:
            parsed = _coerce_transit_int(item)
            if parsed is None:
                return None
            numbers.append(parsed)
        if len(numbers) == 1:
            low = high = numbers[0]
        else:
            low, high = numbers
    else:
        parsed = _coerce_transit_int(value)
        if parsed is None:
            return None
        low = high = parsed

    if low < 0 or high < 0:
        return None
    return (low, high) if low <= high else (high, low)


def _load_shipping_method_transit_map() -> Dict[str, tuple[int, int]]:
    raw = os.getenv("SHIPPING_METHOD_TRANSIT_MAP_JSON")
    if not raw:
        return DEFAULT_SHIPPING_METHOD_TRANSIT_MAP

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        LOGGER.error(
            "Invalid SHIPPING_METHOD_TRANSIT_MAP_JSON; using defaults. error=%s",
            exc,
        )
        return DEFAULT_SHIPPING_METHOD_TRANSIT_MAP

    if not isinstance(parsed, dict):
        LOGGER.error(
            "Invalid SHIPPING_METHOD_TRANSIT_MAP_JSON; expected object. Using defaults."
        )
        return DEFAULT_SHIPPING_METHOD_TRANSIT_MAP

    normalized: Dict[str, tuple[int, int]] = {}
    for key, value in parsed.items():
        key_text = str(key).strip().lower()
        if not key_text:
            continue
        window = _normalize_transit_window(value)
        if window is None:
            LOGGER.warning(
                "Invalid transit window for key '%s' in SHIPPING_METHOD_TRANSIT_MAP_JSON; skipping.",
                key_text,
            )
            continue
        normalized[key_text] = window

    if not normalized:
        LOGGER.error(
            "SHIPPING_METHOD_TRANSIT_MAP_JSON contained no valid entries; using defaults."
        )
        return DEFAULT_SHIPPING_METHOD_TRANSIT_MAP

    return normalized


def _match_transit_window(
    lowered_method: str, transit_map: Dict[str, tuple[int, int]]
) -> Optional[tuple[int, int]]:
    matches: list[tuple[str, tuple[int, int]]] = []
    for key, window in transit_map.items():
        if key and key in lowered_method:
            matches.append((key, window))

    if not matches:
        return None

    if any(char.isdigit() for char in lowered_method):
        digit_matches = [
            match
            for match in matches
            if any(char.isdigit() for char in match[0])
        ]
        if digit_matches:
            matches = digit_matches

    best_key, best_window = sorted(
        matches,
        key=lambda item: (-len(item[0]), item[1][1], item[1][0], item[0]),
    )[0]
    return best_window


def normalize_shipping_method(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Normalize a shipping method string into a bucket + SLA window.

    Returns:
        dict with keys: bucket, min_days, max_days, raw_method, normalized_method
    """
    if raw is None:
        return None

    method = str(raw).strip()
    if not method:
        return None

    lowered = method.lower()
    numeric_window = parse_transit_days(lowered)
    if numeric_window:
        min_days, max_days = numeric_window
        bucket = "Priority" if max_days <= 2 else "Standard"
        normalized_method = format_eta_window(min_days, max_days)
        return {
            "bucket": bucket,
            "min_days": min_days,
            "max_days": max_days,
            "raw_method": method,
            "normalized_method": normalized_method,
        }

    transit_map = _load_shipping_method_transit_map()
    mapped_window = _match_transit_window(lowered, transit_map)
    if mapped_window:
        min_days, max_days = mapped_window
        bucket = "Priority" if max_days <= 2 else "Standard"
        normalized_method = f"{bucket} ({format_eta_window(min_days, max_days)})"
        return {
            "bucket": bucket,
            "min_days": min_days,
            "max_days": max_days,
            "raw_method": method,
            "normalized_method": normalized_method,
        }

    return None


def format_eta_window(min_days: int, max_days: int) -> str:
    if min_days == max_days:
        suffix = "" if min_days == 1 else "s"
        return f"{min_days} business day{suffix}"
    return f"{min_days}-{max_days} business days"


def compute_delivery_estimate(
    order_created_at: Any, shipping_method: Any, inquiry_date: Any
) -> Optional[Dict[str, Any]]:
    """Compute ETA window for an order with no tracking."""
    if not order_created_at or not shipping_method or not inquiry_date:
        return None

    try:
        order_date = _coerce_date(order_created_at)
        inquiry = _coerce_date(inquiry_date)
    except ValueError:
        return None

    if inquiry < order_date:
        return None

    window = normalize_shipping_method(shipping_method)
    if not window:
        return None

    elapsed = business_days_between(order_date, inquiry)
    remaining_min = max(0, window["min_days"] - elapsed)
    remaining_max = max(0, window["max_days"] - elapsed)
    is_late = elapsed >= window["max_days"]
    eta_human = (
        "should arrive any day now"
        if is_late
        else format_eta_window(remaining_min, remaining_max)
    )

    return {
        "bucket": window["bucket"],
        "window_min_days": window["min_days"],
        "window_max_days": window["max_days"],
        "raw_method": window["raw_method"],
        "normalized_method": window["normalized_method"],
        "order_created_date": order_date.isoformat(),
        "inquiry_date": inquiry.isoformat(),
        "elapsed_business_days": elapsed,
        "remaining_min_days": remaining_min,
        "remaining_max_days": remaining_max,
        "eta_human": eta_human,
        "is_late": is_late,
    }


def _normalize_carrier_name(carrier: str) -> str:
    normalized = re.sub(r"[^a-z0-9]", "", str(carrier).lower())
    return normalized


def build_tracking_url(
    carrier: str | None, tracking_number: str | None
) -> Optional[str]:
    if not carrier or not tracking_number:
        return None
    tracking_value = str(tracking_number).strip()
    if not tracking_value:
        return None

    normalized_carrier = _normalize_carrier_name(carrier)
    if not normalized_carrier:
        return None

    encoded_tracking = quote(tracking_value, safe="")
    if "fedex" in normalized_carrier or "federalexpress" in normalized_carrier:
        return f"https://www.fedex.com/fedextrack/?trknbr={encoded_tracking}"
    if "usps" in normalized_carrier or "unitedstatespostalservice" in normalized_carrier:
        return f"https://tools.usps.com/go/TrackConfirmAction?tLabels={encoded_tracking}"
    if "ups" in normalized_carrier or "unitedparcelservice" in normalized_carrier:
        return f"https://www.ups.com/track?loc=en_US&tracknum={encoded_tracking}"
    if "dhl" in normalized_carrier or "dhlexpress" in normalized_carrier:
        return (
            "https://www.dhl.com/global-en/home/tracking.html"
            f"?tracking-id={encoded_tracking}"
        )
    return None


def build_carrier_tracking_url(
    carrier: str, tracking_number: str
) -> Optional[str]:
    return build_tracking_url(carrier, tracking_number)


def build_tracking_reply(order_summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Construct a deterministic draft reply for tracking-present order status cases.
    Returns None if no tracking signal is present.

    Note: when we can deterministically build a carrier tracking URL, we persist it
    on the provided order_summary so downstream consumers can reuse it.
    """
    tracking_number = (
        order_summary.get("tracking_number")
        or order_summary.get("tracking")
        or order_summary.get("tracking_no")
        or order_summary.get("trackingCode")
    )
    if isinstance(tracking_number, (list, dict)):
        tracking_number = None
    if isinstance(tracking_number, str) and tracking_number.strip() in {"[]", "none", "null"}:
        tracking_number = None
    tracking_url = (
        order_summary.get("tracking_url")
        or order_summary.get("tracking_link")
        or order_summary.get("status_url")
        or order_summary.get("trackingUrl")
    )
    carrier = (
        order_summary.get("carrier")
        or order_summary.get("shipping_carrier")
        or order_summary.get("carrier_name")
        or order_summary.get("carrierName")
    )
    shipping_method = (
        order_summary.get("shipping_method")
        or order_summary.get("shipping_method_name")
        or order_summary.get("shipping_service")
        or order_summary.get("shipping_option")
    )
    shipping_method = normalize_shipping_method_for_carrier(shipping_method, carrier)

    # Require at least one tracking signal; don't fabricate.
    if not tracking_number and not tracking_url and not carrier:
        return None

    if not tracking_url and tracking_number and carrier:
        generated_url = build_tracking_url(carrier, tracking_number)
        if generated_url:
            tracking_url = generated_url
            order_summary["tracking_url"] = generated_url

    tn = tracking_number or "(not available)"
    cr = carrier or "(not available)"
    link = tracking_url or "(not available)"
    sm = shipping_method

    shipping_line = f"- Shipping method: {sm}\n" if sm else ""
    body = (
        "Thanks for reaching out — here’s the latest tracking information for your order:\n\n"
        f"- Carrier: {cr}\n"
        f"- Tracking number: {tn}\n"
        f"- Tracking link: {link}\n"
        f"{shipping_line}\n"
        "If the link doesn’t show updates yet, please try again in a few hours — carrier scans can take time to appear."
    )

    return {
        "body": body.strip(),
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "carrier": carrier,
        "shipping_method": shipping_method,
    }


def normalize_shipping_method_for_carrier(
    shipping_method: Optional[str], carrier: Optional[str]
) -> Optional[str]:
    """
    Normalize the shipping method label to align with the actual carrier when they conflict.

    Example: "USPS/UPS® Ground" + carrier "FedEx" -> "FedEx Ground"
    """
    if not carrier:
        return shipping_method
    carrier_text = str(carrier).strip()
    if not carrier_text:
        return shipping_method

    if not shipping_method:
        return carrier_text
    method_text = str(shipping_method).strip()
    if not method_text:
        return carrier_text

    normalized_method = _normalize_carrier_name(method_text)
    normalized_carrier = _normalize_carrier_name(carrier_text)
    if normalized_carrier and normalized_carrier in normalized_method:
        return method_text

    # Strip known carrier tokens from the method label and keep the service portion.
    cleaned = re.sub(r"\b(usps|ups|fedex|dhl)\b", " ", method_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", cleaned).strip()
    if cleaned:
        return f"{carrier_text} {cleaned}"
    return carrier_text


def build_no_tracking_reply(
    order_summary: Optional[Dict[str, Any]],
    *,
    inquiry_date: Any,
    delivery_estimate: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Construct a deterministic draft reply for no-tracking order status cases.
    """
    summary = order_summary if isinstance(order_summary, dict) else {}
    estimate = delivery_estimate or compute_delivery_estimate(
        summary.get("created_at") or summary.get("order_created_at"),
        summary.get("shipping_method") or summary.get("shipping_method_name"),
        inquiry_date,
    )

    raw_order_id = summary.get("order_id") or summary.get("id")
    order_id = str(raw_order_id).strip() if raw_order_id is not None else ""
    has_order_id = bool(order_id) and order_id.lower() not in {"unknown", "your order"}

    if estimate:
        order_date_human = estimate["order_created_date"]
        method_label = estimate["normalized_method"] or estimate["raw_method"]

        if estimate["is_late"]:
            eta_sentence = "It is already beyond the expected window, so it should arrive any day now."
        else:
            eta_sentence = f"It should arrive in about {estimate['eta_human']}."

        order_label = f"Order {order_id}" if has_order_id else "Your order"
        body = (
            f"Thanks for your patience. {order_label} was placed on {order_date_human}. "
            f"With {method_label} shipping, {eta_sentence} "
            "We'll send tracking as soon as it ships."
        )

        return {
            "body": body.strip(),
            "eta_human": estimate["eta_human"],
            "bucket": estimate["bucket"],
            "is_late": estimate["is_late"],
        }

    if not has_order_id:
        fallback_body = (
            "Thanks for reaching out. We don't have tracking details available yet. "
            "A support agent will follow up shortly."
        )
    else:
        fallback_body = (
            "Thanks for your patience. We don't have tracking updates yet. "
            "We'll send tracking as soon as it's ready."
        )

    return {
        "body": fallback_body.strip(),
        "eta_human": None,
        "bucket": None,
        "is_late": None,
    }


__all__ = [
    "add_business_days",
    "build_carrier_tracking_url",
    "build_tracking_url",
    "build_tracking_reply",
    "build_no_tracking_reply",
    "business_days_between",
    "compute_delivery_estimate",
    "parse_transit_days",
    "format_eta_window",
    "normalize_shipping_method",
]
