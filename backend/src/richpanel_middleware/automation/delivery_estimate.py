from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional


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
    numeric_window = _parse_numeric_window(lowered)
    if numeric_window:
        min_days, max_days = numeric_window
        bucket = "Priority" if max_days <= 2 else "Standard"
        normalized_method = (
            f"{min_days}-{max_days} business days"
            if min_days != max_days
            else f"{min_days} business day" + ("" if min_days == 1 else "s")
        )
        return {
            "bucket": bucket,
            "min_days": min_days,
            "max_days": max_days,
            "raw_method": method,
            "normalized_method": normalized_method,
        }

    keyword_windows = [
        (("priority", "overnight", "next day", "next-day", "express", "rush", "rushed", "1-day", "1 day"), (1, 1), "Priority"),
        (("2-day", "2 day", "two day"), (2, 2), "Priority"),
        (("standard", "ground"), (3, 5), "Standard"),
        (("economy", "free", "postal", "mail"), (5, 7), "Standard"),
    ]
    for keywords, window, bucket in keyword_windows:
        if any(keyword in lowered for keyword in keywords):
            min_days, max_days = window
            normalized_method = f"{bucket} ({min_days}-{max_days} business days)"
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
    eta_human = "should arrive any day now" if is_late else format_eta_window(remaining_min, remaining_max)

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


def build_no_tracking_reply(
    order_summary: Dict[str, Any],
    *,
    inquiry_date: Any,
    delivery_estimate: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Construct a deterministic draft reply for no-tracking order status cases.
    """
    estimate = delivery_estimate or compute_delivery_estimate(
        order_summary.get("created_at") or order_summary.get("order_created_at"),
        order_summary.get("shipping_method") or order_summary.get("shipping_method_name"),
        inquiry_date,
    )

    if not estimate:
        return None

    order_id = str(order_summary.get("order_id") or order_summary.get("id") or "your order")
    order_date_human = estimate["order_created_date"]
    method_label = estimate["normalized_method"] or estimate["raw_method"]

    if estimate["is_late"]:
        eta_sentence = "It is already beyond the expected window, so it should arrive any day now."
    else:
        eta_sentence = f"It should arrive in about {estimate['eta_human']}."

    body = (
        f"Thanks for your patience. Order {order_id} was placed on {order_date_human}. "
        f"With {method_label} shipping, {eta_sentence} "
        "We'll send tracking as soon as it ships."
    )

    return {
        "body": body.strip(),
        "eta_human": estimate["eta_human"],
        "bucket": estimate["bucket"],
        "is_late": estimate["is_late"],
    }


__all__ = [
    "add_business_days",
    "build_no_tracking_reply",
    "business_days_between",
    "compute_delivery_estimate",
    "format_eta_window",
    "normalize_shipping_method",
]

