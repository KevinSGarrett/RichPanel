from __future__ import annotations

import json
import logging
import os
import re
from urllib.parse import quote
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

ETA_FLOOR_MIN_DAYS = 1
ETA_FLOOR_MAX_DAYS = 2

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

_PREORDER_TAG_TOKENS = {"pre-order", "preorder", "pre order"}
_PREORDER_DELIVERY_METHODS = {
    "pre order delivery",
    "preorder delivery",
    "pre-order delivery",
}


def _is_expedited_24h(shipping_method: Optional[str]) -> bool:
    if not shipping_method:
        return False
    lowered = str(shipping_method).lower()
    tokens = (
        "rush",
        "overnight",
        "express",
        "priority",
        "next day",
        "next-day",
        "1 day",
        "1-day",
    )
    explicit_multi_day = bool(
        re.search(r"(?:[2-9]|[1-9][0-9]+)\s*[-]?\s*day", lowered)
        or re.search(
            r"(two|three|four|five|six|seven|eight|nine)[\s-]*day", lowered
        )
    )
    if explicit_multi_day:
        return False
    return any(token in lowered for token in tokens)


def _processing_window_for_method(shipping_method: Optional[str]) -> tuple[int, int, str]:
    if _is_expedited_24h(shipping_method):
        return 1, 1, "24 business hours"
    return 3, 5, format_eta_window(3, 5)


def has_preorder_tag(order_tags: Any, order_tags_raw: Any = None) -> bool:
    tokens: List[str] = []
    if isinstance(order_tags, list):
        tokens = [token for token in order_tags if isinstance(token, str)]
    elif isinstance(order_tags_raw, str):
        tokens = [token for token in order_tags_raw.split(",")]
    else:
        return False

    if not tokens and isinstance(order_tags_raw, str):
        tokens = [token for token in order_tags_raw.split(",")]

    for token in tokens:
        normalized = " ".join(token.strip().lower().split())
        if normalized in _PREORDER_TAG_TOKENS:
            return True
    return False


def _format_long_date(value: date) -> str:
    return f"{value.strftime('%A, %B')} {value.day}, {value.year}"


def _format_delivery_window(start: date, end: date) -> str:
    if start == end:
        return f"{start.strftime('%B')} {start.day}, {start.year}"
    if start.year == end.year:
        return (
            f"{start.strftime('%B')} {start.day}\u2013"
            f"{end.strftime('%B')} {end.day}, {start.year}"
        )
    return (
        f"{start.strftime('%B')} {start.day}, {start.year}"
        f"\u2013{end.strftime('%B')} {end.day}, {end.year}"
    )


def _format_day_window(min_days: int, max_days: int) -> str:
    if min_days == max_days:
        return f"{min_days} days"
    return f"{min_days}\u2013{max_days} days"


def _normalize_preorder_delivery_method(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    text = " ".join(text.split())
    text = re.sub(r"\s*-\s*", "-", text)
    return text


def _preorder_delivery_fallback_window(
    shipping_method: Any,
) -> Optional[Dict[str, Any]]:
    normalized = _normalize_preorder_delivery_method(shipping_method)
    if normalized not in _PREORDER_DELIVERY_METHODS:
        return None
    raw_method = str(shipping_method).strip()
    # Preorder fallback window is intentionally fixed per B83 requirements.
    # Source: REHYDRATION_PACK/RUNS/RUN_20260215_2351Z/A/RUN_REPORT.md
    min_days = 3
    max_days = 7
    bucket = "Standard"
    normalized_method = f"{bucket} ({format_eta_window(min_days, max_days)})"
    return {
        "bucket": bucket,
        "min_days": min_days,
        "max_days": max_days,
        "raw_method": raw_method,
        "normalized_method": normalized_method,
    }


def _effective_transit_window(shipping_method: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return transit window, overriding to 1–1 business day for expedited methods."""
    window = normalize_shipping_method(shipping_method)
    if not window:
        return None
    if not _is_expedited_24h(shipping_method):
        return window
    return {
        "bucket": "Priority",
        "min_days": 1,
        "max_days": 1,
        "raw_method": window["raw_method"],
        "normalized_method": f"Priority ({format_eta_window(1, 1)})",
    }


def compute_preorder_delivery_estimate(
    order_created_at: Any,
    shipping_method: Any,
    inquiry_date: Any,
    order_tags: Any = None,
    order_tags_raw: Any = None,
) -> Optional[Dict[str, Any]]:
    """Compute a tag-based preorder delivery window (ship date = order_date + 45 days)."""
    if not has_preorder_tag(order_tags, order_tags_raw):
        return None
    if not order_created_at or not inquiry_date:
        return None

    try:
        order_date = _coerce_date(order_created_at)
        inquiry = _coerce_date(inquiry_date)
    except ValueError:
        return None

    # Release date is a calendar offset; processing/transit remain business-day based.
    release_date = order_date + timedelta(days=45)
    release_date_human = _format_long_date(release_date)
    release_in_days = (release_date - inquiry).days
    ship_days_from_inquiry_human = (
        _format_day_window(release_in_days, release_in_days)
        if release_in_days >= 0
        else None
    )

    processing_min, processing_max, processing_human = _processing_window_for_method(
        shipping_method
    )

    window = _effective_transit_window(shipping_method)
    if not window:
        window = _preorder_delivery_fallback_window(shipping_method)
    if not window:
        # Fail closed for preorder: ship date only, no delivery window.
        return {
            "order_created_date": order_date.isoformat(),
            "inquiry_date": inquiry.isoformat(),
            "preorder": True,
            "preorder_ship_date_human": release_date_human,
            "ship_days_from_inquiry_human": ship_days_from_inquiry_human,
            "eta_human": None,
        }

    transit_min, transit_max = window["min_days"], window["max_days"]
    total_min = processing_min + transit_min
    total_max = processing_max + transit_max
    delivery_min = add_business_days(release_date, total_min)
    delivery_max = add_business_days(release_date, total_max)
    delivery_window_human = _format_delivery_window(delivery_min, delivery_max)
    days_min = (delivery_min - inquiry).days
    days_max = (delivery_max - inquiry).days
    if days_max < 0:
        days_from_inquiry_human = None
    else:
        days_from_inquiry_human = _format_day_window(max(0, days_min), max(0, days_max))
    is_late = inquiry >= delivery_max
    eta_human = "should arrive any day now" if is_late else delivery_window_human

    return {
        "bucket": window["bucket"],
        "window_min_days": total_min,
        "window_max_days": total_max,
        "processing_min_days": processing_min,
        "processing_max_days": processing_max,
        "processing_human": processing_human,
        "transit_min_days": transit_min,
        "transit_max_days": transit_max,
        "raw_method": window["raw_method"],
        "normalized_method": window["normalized_method"],
        "order_created_date": order_date.isoformat(),
        "inquiry_date": inquiry.isoformat(),
        "eta_human": eta_human,
        "is_late": is_late,
        "preorder": True,
        "preorder_ship_date_human": release_date_human,
        "delivery_window_human": delivery_window_human,
        "days_from_inquiry_human": days_from_inquiry_human,
        "ship_days_from_inquiry_human": ship_days_from_inquiry_human,
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
    range_match = re.search(r"([0-9]+)\s*(?:-|\u2013|to)\s*([0-9]+)", text)
    if range_match:
        first, second = int(range_match.group(1)), int(range_match.group(2))
        return (first, second) if first <= second else (second, first)

    single_match = re.search(
        r"([0-9]+)\s*[-]?\s*(?:business\s+days?|bd|days?)", text
    )
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


_BUSINESS_DAYS_NOTE = "(Business days are Mon–Fri; holidays may affect timelines.)"
_TRACKING_EMAIL_LINE = (
    "Tracking will be emailed automatically once it ships and is scanned by the carrier."
)


def _normalize_shipping_label(
    *, estimate: Dict[str, Any], fallback_method: Optional[str] = None
) -> Optional[str]:
    bucket = estimate.get("bucket")
    if isinstance(bucket, str) and bucket.strip():
        return bucket.strip()
    method = (
        estimate.get("normalized_method")
        or estimate.get("raw_method")
        or fallback_method
    )
    if isinstance(method, str) and method.strip():
        cleaned = re.sub(r"\s*\(.*?\)\s*$", "", method).strip()
        return cleaned or None
    return None


def _build_no_tracking_timeline_paragraph(
    estimate: Dict[str, Any], *, fallback_method: Optional[str] = None
) -> Optional[str]:
    if not isinstance(estimate, dict):
        return None

    processing_human = estimate.get("processing_human")
    transit_min_days = estimate.get("transit_min_days")
    transit_max_days = estimate.get("transit_max_days")
    delivery_window_human = estimate.get("delivery_window_human")

    if isinstance(delivery_window_human, str) and not delivery_window_human.strip():
        delivery_window_human = None

    if not delivery_window_human:
        return None

    method_label = _normalize_shipping_label(
        estimate=estimate, fallback_method=fallback_method
    )
    shipping_window = None
    if transit_min_days is not None and transit_max_days is not None:
        shipping_window = format_eta_window(transit_min_days, transit_max_days)
    if not processing_human or not shipping_window:
        return None

    if estimate.get("preorder"):
        days_from_inquiry_human = estimate.get("days_from_inquiry_human")
        sentences = [
            f"After release, processing typically takes {processing_human}.",
        ]
        if method_label:
            sentences.append(f"{method_label} shipping usually takes {shipping_window}.")
        else:
            sentences.append(f"Shipping usually takes {shipping_window}.")
        sentences.append(f"Delivery is estimated for {delivery_window_human}.")
        if days_from_inquiry_human:
            sentences.append(f"That's about {days_from_inquiry_human} from today.")
        sentences.append(_BUSINESS_DAYS_NOTE)
        return " ".join(sentences)

    window_min_days = estimate.get("window_min_days")
    window_max_days = estimate.get("window_max_days")
    total_window = None
    if window_min_days is not None and window_max_days is not None:
        total_window = format_eta_window(window_min_days, window_max_days)

    sentences = [f"Processing typically takes {processing_human}."]
    if method_label:
        sentences.append(f"{method_label} shipping usually takes {shipping_window}.")
    else:
        sentences.append(f"Shipping usually takes {shipping_window}.")
    sentences.append(f"Delivery is estimated for {delivery_window_human}.")
    if total_window:
        sentences.append(f"That's about {total_window} total.")
    sentences.append(_BUSINESS_DAYS_NOTE)
    return " ".join(sentences)


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

    window = _effective_transit_window(shipping_method)
    if not window:
        return None

    processing_min, processing_max, processing_human = _processing_window_for_method(
        shipping_method
    )
    transit_min, transit_max = window["min_days"], window["max_days"]
    total_min = processing_min + transit_min
    total_max = processing_max + transit_max

    elapsed = business_days_between(order_date, inquiry)
    remaining_min = max(0, total_min - elapsed)
    remaining_max = max(0, total_max - elapsed)
    is_late = elapsed >= total_max
    if not is_late:
        # Floor avoids confusing "0-1 business days" messaging per B86 requirements.
        # Clamp min to max after flooring to avoid inverted ranges.
        if remaining_min < ETA_FLOOR_MIN_DAYS:
            remaining_min = ETA_FLOOR_MIN_DAYS
        if remaining_max < ETA_FLOOR_MAX_DAYS:
            remaining_max = ETA_FLOOR_MAX_DAYS
        remaining_min = min(remaining_min, remaining_max)
    eta_human = (
        "should arrive any day now"
        if is_late
        else format_eta_window(remaining_min, remaining_max)
    )
    delivery_min_date = add_business_days(order_date, total_min)
    delivery_max_date = add_business_days(order_date, total_max)
    delivery_window_human = _format_delivery_window(
        delivery_min_date, delivery_max_date
    )

    return {
        "bucket": window["bucket"],
        "window_min_days": total_min,
        "window_max_days": total_max,
        "processing_min_days": processing_min,
        "processing_max_days": processing_max,
        "processing_human": processing_human,
        "transit_min_days": transit_min,
        "transit_max_days": transit_max,
        "raw_method": window["raw_method"],
        "normalized_method": window["normalized_method"],
        "order_created_date": order_date.isoformat(),
        "inquiry_date": inquiry.isoformat(),
        "elapsed_business_days": elapsed,
        "remaining_min_days": remaining_min,
        "remaining_max_days": remaining_max,
        "eta_human": eta_human,
        "is_late": is_late,
        "delivery_window_human": delivery_window_human,
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

    detail_sentences: List[str] = []
    if cr != "(not available)":
        detail_sentences.append(f"It's going out with {cr}.")
    if tn != "(not available)":
        detail_sentences.append(f"Tracking number: {tn}.")
    if sm:
        detail_sentences.append(f"Shipping method: {sm}.")

    paragraphs: List[str] = ["Your order has shipped and tracking is available."]
    if detail_sentences:
        paragraphs.append(" ".join(detail_sentences))
    paragraphs.append(f"Tracking link: {link}")
    paragraphs.append("Carrier scans can take a few hours to appear in tracking.")
    body = "\n\n".join(paragraphs)

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
        return None
    method_text = str(shipping_method).strip()
    if not method_text:
        return None

    normalized_carrier = _normalize_carrier_name(carrier_text)
    if normalized_carrier:
        if normalized_carrier in {"ups", "usps", "fedex", "dhl"}:
            if re.search(
                rf"\b{re.escape(normalized_carrier)}\b",
                method_text,
                flags=re.IGNORECASE,
            ):
                return method_text
        else:
            normalized_method = _normalize_carrier_name(method_text)
            if normalized_carrier in normalized_method:
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
    preorder_tagged = has_preorder_tag(
        summary.get("order_tags"),
        summary.get("order_tags_raw") or summary.get("tags"),
    )
    preorder_estimate = (
        delivery_estimate
        if isinstance(delivery_estimate, dict) and delivery_estimate.get("preorder")
        else None
    )
    if preorder_estimate is None and preorder_tagged:
        preorder_estimate = compute_preorder_delivery_estimate(
            summary.get("created_at") or summary.get("order_created_at"),
            summary.get("shipping_method") or summary.get("shipping_method_name"),
            inquiry_date,
            summary.get("order_tags"),
            summary.get("order_tags_raw") or summary.get("tags"),
        )
    has_preorder = bool(preorder_estimate or preorder_tagged)
    estimate = None
    if not has_preorder:
        estimate = delivery_estimate or compute_delivery_estimate(
            summary.get("created_at") or summary.get("order_created_at"),
            summary.get("shipping_method") or summary.get("shipping_method_name"),
            inquiry_date,
        )

    raw_order_id = summary.get("order_id") or summary.get("id")
    order_id = str(raw_order_id).strip() if raw_order_id is not None else ""
    has_order_id = bool(order_id) and order_id.lower() not in {"unknown", "your order"}

    if has_preorder and preorder_estimate:
        ship_date_human = preorder_estimate.get("preorder_ship_date_human")
        if isinstance(ship_date_human, str) and not ship_date_human.strip():
            ship_date_human = None
        delivery_window_human = preorder_estimate.get("delivery_window_human")
        days_from_inquiry_human = preorder_estimate.get("days_from_inquiry_human")
        ship_days_from_inquiry_human = preorder_estimate.get(
            "ship_days_from_inquiry_human"
        )
        processing_human = preorder_estimate.get("processing_human")
        is_late = bool(preorder_estimate.get("is_late"))
        method_label = summary.get("shipping_method") or summary.get(
            "shipping_method_name"
        )

        if ship_date_human:
            body = (
                "Your order includes a pre-order item that releases on "
                f"{ship_date_human}"
            )
            if ship_days_from_inquiry_human:
                body = f"{body} (in {ship_days_from_inquiry_human})."
            else:
                body = f"{body}."
        else:
            body = "Your order includes a pre-order item."

        if is_late:
            body = (
                f"{body}\n\n"
                "It is already beyond the expected window, so it should arrive any day now."
            )
        else:
            timeline = _build_no_tracking_timeline_paragraph(
                preorder_estimate, fallback_method=method_label
            )
            if timeline:
                body = f"{body}\n\n{timeline}"

        return {
            "body": f"{body}\n\n{_TRACKING_EMAIL_LINE}".strip(),
            "eta_human": delivery_window_human,
            "bucket": preorder_estimate.get("bucket"),
            "is_late": preorder_estimate.get("is_late"),
        }

    if estimate:
        order_date_human = estimate["order_created_date"]
        order_label = f"Order {order_id}" if has_order_id else "Your order"
        body = (
            f"We don't have tracking yet for {order_label} (placed on {order_date_human})."
        )
        if estimate["is_late"]:
            body = (
                f"{body}\n\n"
                "It is already beyond the expected window, so it should arrive any day now."
            )
        else:
            method_label = summary.get("shipping_method") or summary.get(
                "shipping_method_name"
            )
            timeline = _build_no_tracking_timeline_paragraph(
                estimate, fallback_method=method_label
            )
            if timeline:
                body = f"{body}\n\n{timeline}"

        return {
            "body": f"{body}\n\n{_TRACKING_EMAIL_LINE}".strip(),
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
    "compute_preorder_delivery_estimate",
    "compute_delivery_estimate",
    "has_preorder_tag",
    "parse_transit_days",
    "format_eta_window",
    "normalize_shipping_method",
]
