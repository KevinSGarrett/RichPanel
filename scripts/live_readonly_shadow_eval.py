#!/usr/bin/env python3
"""
Live Read-Only Shadow Evaluation

Reads real Richpanel + Shopify data for a small ticket sample without allowing any writes.
Fails closed via environment guards + read-only request tracing.
Produces PII-safe JSON + markdown artifacts under artifacts/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

try:
    import boto3  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.pipeline import plan_actions, normalize_event  # type: ignore
from richpanel_middleware.commerce.order_lookup import lookup_order_summary  # type: ignore
from richpanel_middleware.automation.delivery_estimate import (  # type: ignore
    compute_delivery_estimate,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # type: ignore
from richpanel_middleware.automation.pipeline import _missing_order_context  # type: ignore
from richpanel_middleware.automation.router import extract_customer_message  # type: ignore
from richpanel_middleware.integrations.richpanel.client import (  # type: ignore
    RichpanelClient,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)
from richpanel_middleware.integrations.shopify import (  # type: ignore
    ShopifyClient,
    ShopifyRequestError,
    TransportError as ShopifyTransportError,
)
from readonly_shadow_utils import (
    build_route_info as _build_route_info,
    comment_is_operator as _comment_is_operator,
    extract_comment_message as _extract_comment_message,
    extract_order_number,
    fetch_recent_ticket_refs as _fetch_recent_ticket_refs,
    safe_error as _safe_error,
    summarize_comment_metadata,
)
LOGGER = logging.getLogger("readonly_shadow_eval")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("richpanel_middleware").setLevel(logging.WARNING)
logging.getLogger("integrations").setLevel(logging.WARNING)

PROD_RICHPANEL_BASE_URL = "https://api.richpanel.com"


def _env_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _hash_api_key(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:8]


def _build_identity_block(
    *,
    client: RichpanelClient,
    env_name: str,
    started_at: datetime,
    duration_seconds: float,
) -> Dict[str, Any]:
    api_key_hash = None
    api_key_error = None
    try:
        api_key_hash = _hash_api_key(client._load_api_key())  # type: ignore[attr-defined]
    except Exception as exc:
        api_key_error = exc.__class__.__name__
    return {
        "richpanel_base_url": getattr(client, "base_url", None),
        "mw_env": os.environ.get("MW_ENV") or os.environ.get("ENVIRONMENT"),
        "richpanel_env": os.environ.get("RICHPANEL_ENV"),
        "resolved_env": env_name,
        "api_key_secret_id": getattr(client, "api_key_secret_id", None),
        "api_key_hash": api_key_hash,
        "api_key_error": api_key_error,
        "run_started_at": started_at.isoformat(),
        "run_duration_seconds": round(duration_seconds, 3),
    }


def _max_requests_in_window(timestamps: List[float], window_seconds: int) -> int:
    if not timestamps:
        return 0
    timestamps = sorted(timestamps)
    max_count = 0
    start_idx = 0
    for end_idx, end_ts in enumerate(timestamps):
        while end_ts - timestamps[start_idx] > window_seconds:
            start_idx += 1
        max_count = max(max_count, end_idx - start_idx + 1)
    return max_count


def _summarize_request_burst(
    entries: List[Dict[str, Any]],
    *,
    window_seconds: int = 30,
    max_endpoints: int = 10,
) -> Dict[str, Any]:
    if not entries:
        return {}
    timestamps = [entry["timestamp"] for entry in entries if entry.get("timestamp")]
    max_overall = _max_requests_in_window(timestamps, window_seconds)
    by_endpoint: Dict[str, List[float]] = {}
    for entry in entries:
        path = entry.get("path")
        ts = entry.get("timestamp")
        if not path or not ts:
            continue
        by_endpoint.setdefault(path, []).append(ts)
    endpoint_bursts: list[Dict[str, Any]] = []
    for path, times in by_endpoint.items():
        endpoint_bursts.append(
            {
                "path": path,
                "max_requests": _max_requests_in_window(times, window_seconds),
                "total_requests": len(times),
            }
        )
    endpoint_bursts.sort(key=lambda item: item["max_requests"], reverse=True)
    return {
        "window_seconds": window_seconds,
        "max_requests_overall": max_overall,
        "max_requests_by_endpoint": endpoint_bursts[:max_endpoints],
    }


def _summarize_retry_after(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    violations = 0
    comparisons: list[float] = []
    for entry in entries:
        retry_after = entry.get("retry_after")
        retry_delay = entry.get("retry_delay_seconds")
        if retry_after is None or retry_delay is None:
            continue
        try:
            retry_after_val = float(retry_after)
            retry_delay_val = float(retry_delay)
        except (TypeError, ValueError):
            continue
        comparisons.append(retry_delay_val - retry_after_val)
        if retry_delay_val + 0.001 < retry_after_val:
            violations += 1
    if not comparisons:
        return {"checked": 0, "violations": 0}
    return {
        "checked": len(comparisons),
        "violations": violations,
        "min_delta_seconds": round(min(comparisons), 3),
        "max_delta_seconds": round(max(comparisons), 3),
    }

REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
    "RICHPANEL_READ_ONLY": "true",
    "RICHPANEL_OUTBOUND_ENABLED": "false",
}

ALLOWED_PROD_ENVS = {"prod", "production"}
DEFAULT_SAMPLE_SIZE = 10
DRIFT_WARNING_THRESHOLD = 0.2
SUMMARY_TOP_FAILURE_REASONS = 5
SCHEMA_KEY_DEPTH_LIMIT = 5
SCHEMA_KEY_STATS_LIMIT = 25
SCHEMA_IGNORE_KEYS = {
    "etag",
    "checksum",
    "signature",
    "token",
    "hash",
    "cursor",
    "page",
    "page_info",
    "pageinfo",
    "per_page",
    "perpage",
    "page_size",
    "pagesize",
    "limit",
    "offset",
    "total",
    "count",
    "next_page",
    "prev_page",
    "previous_page",
    "nextpage",
    "prevpage",
    "previouspage",
    "url",
    "href",
    "link",
    "links",
}
SCHEMA_SKIP_DESCENT_KEYS = {
    "custom_fields",
    "customfields",
    "comments",
    "comment",
    "messages",
    "conversation_messages",
    "conversationmessages",
    "events",
    "history",
    "audit",
    "timeline",
    "notes",
    "note",
    "tags",
    "labels",
    "metadata",
    "meta",
    "attributes",
    "fields",
    "attachments",
    "attachment",
    "links",
    "link",
}
CUSTOM_REPORT_FILENAME = "live_shadow_report.json"
CUSTOM_SUMMARY_JSON_FILENAME = "live_shadow_summary.json"
CUSTOM_SUMMARY_MD_FILENAME = "live_shadow_summary.md"
CUSTOM_TRACE_FILENAME = "live_shadow_http_trace.json"
SEND_ACTION_TYPES = {
    "send_message",
    "send_ticket_reply",
    "send_reply",
    "send_message_failed",
    "send_message_operator_missing",
}
MATCH_FAILURE_BUCKET_KEYS = (
    "no_email",
    "no_order_number",
    "ambiguous_customer",
    "no_order_candidates",
    "order_match_failed",
    "parse_error",
    "api_error",
    "other_failure",
    "unknown",
)
CHAT_CHANNELS = {
    "chat",
    "live_chat",
    "livechat",
    "messenger",
    "facebook",
    "instagram",
    "sms",
    "whatsapp",
    "web",
}

# B61/C: Drift thresholds for diagnostic monitoring (configurable via env vars)
def _get_drift_thresholds() -> Dict[str, float]:
    """
    Get drift thresholds from environment variables or defaults.
    Allows operational tuning without code changes.
    """
    return {
        "match_rate_drop_pct": float(
            os.environ.get("SHADOW_EVAL_MATCH_RATE_DROP_THRESHOLD", "10.0")
        ),
        "api_error_rate_pct": float(
            os.environ.get("SHADOW_EVAL_API_ERROR_RATE_THRESHOLD", "5.0")
        ),
        "order_number_share_drop_pct": float(
            os.environ.get("SHADOW_EVAL_ORDER_NUMBER_DROP_THRESHOLD", "15.0")
        ),
        "schema_drift_new_ratio": float(
            os.environ.get("SHADOW_EVAL_SCHEMA_DRIFT_THRESHOLD", "0.2")
        ),
    }


# Default thresholds (for reference in tests and documentation)
DRIFT_THRESHOLDS = _get_drift_thresholds()


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _openai_shadow_enabled() -> bool:
    return _to_bool(os.environ.get("MW_OPENAI_SHADOW_ENABLED"), False)


def _openai_any_enabled() -> bool:
    return _to_bool(os.environ.get("MW_OPENAI_ROUTING_ENABLED"), False) or _to_bool(
        os.environ.get("MW_OPENAI_INTENT_ENABLED"), False
    ) or _to_bool(os.environ.get("MW_OPENAI_REWRITE_ENABLED"), False)


def _fingerprint(text: str, *, length: int = 12) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest[:length]


def _redact_identifier(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return f"redacted:{_fingerprint(text)}"


def _redact_shop_domain(domain: Optional[str]) -> Optional[str]:
    """Treat shop domain as sensitive; hash for report output."""
    return _redact_identifier(domain)


def _normalize_optional_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        text = str(value).strip()
    except Exception:
        return ""
    return text


def _extract_channel(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    channel = None
    via = payload.get("via")
    if isinstance(via, dict):
        channel = via.get("channel")
    if channel is None:
        channel = payload.get("channel")
    return _normalize_optional_text(channel).lower()


def _classify_channel(channel: str) -> str:
    if not channel:
        return "unknown"
    if channel == "email":
        return "email"
    if channel in CHAT_CHANNELS or "chat" in channel:
        return "chat"
    return "unknown"


def _is_schema_id_key(key: str) -> bool:
    if key in {"id", "_id", "ID"}:
        return True
    if key.endswith(("_id", "_Id", "_ID", "Id", "ID")) and len(key) > 2:
        return True
    return key.lower() in {"uuid", "guid", "gid"}


def _is_schema_timestamp_key(key: str) -> bool:
    lower = key.strip().lower()
    if "timestamp" in lower:
        return True
    if lower.endswith(("_at", "_date", "_time")):
        return True
    if lower in {
        "createdat",
        "updatedat",
        "deletedat",
        "processedat",
        "resolvedat",
        "closedat",
        "openedat",
        "modifiedat",
        "createddate",
        "updateddate",
        "deleteddate",
        "processeddate",
        "resolveddate",
        "closeddate",
        "openeddate",
        "modifieddate",
        "createdtime",
        "updatedtime",
        "deletedtime",
        "processedtime",
        "resolvedtime",
        "closedtime",
        "openedtime",
        "modifiedtime",
    }:
        return True
    return False


def _should_ignore_schema_key(key: str) -> bool:
    normalized = key.strip()
    if not normalized or normalized.isdigit():
        return True
    lower = normalized.lower()
    if lower in SCHEMA_IGNORE_KEYS:
        return True
    if _is_schema_id_key(normalized):
        return True
    if _is_schema_timestamp_key(normalized):
        return True
    return False


def _should_skip_schema_descent(key: str) -> bool:
    return key.strip().lower() in SCHEMA_SKIP_DESCENT_KEYS


def _collect_schema_key_paths(
    payload: Any,
    *,
    keys: set[str],
    ignored_keys: Optional[set[str]] = None,
    collect_only_ignored: bool = False,
    prefix: str = "",
    depth: int = 0,
    max_depth: int = SCHEMA_KEY_DEPTH_LIMIT,
) -> None:
    if depth > max_depth:
        return
    if collect_only_ignored and ignored_keys is None:
        return
    if isinstance(payload, dict):
        for raw_key, value in payload.items():
            key = _normalize_optional_text(raw_key)
            if not key or key.startswith("__"):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if collect_only_ignored:
                ignored_keys.add(path)
                if isinstance(value, list):
                    ignored_keys.add(f"{path}[]")
                _collect_schema_key_paths(
                    value,
                    keys=keys,
                    ignored_keys=ignored_keys,
                    collect_only_ignored=True,
                    prefix=path,
                    depth=depth + 1,
                    max_depth=max_depth,
                )
                continue
            if _should_ignore_schema_key(key):
                if ignored_keys is not None:
                    ignored_keys.add(path)
                    if isinstance(value, list):
                        ignored_keys.add(f"{path}[]")
                continue
            keys.add(path)
            if _should_skip_schema_descent(key):
                if isinstance(value, list):
                    keys.add(f"{path}[]")
                if ignored_keys is not None:
                    _collect_schema_key_paths(
                        value,
                        keys=keys,
                        ignored_keys=ignored_keys,
                        collect_only_ignored=True,
                        prefix=path,
                        depth=depth + 1,
                        max_depth=max_depth,
                    )
                continue
            _collect_schema_key_paths(
                value,
                keys=keys,
                ignored_keys=ignored_keys,
                collect_only_ignored=collect_only_ignored,
                prefix=path,
                depth=depth + 1,
                max_depth=max_depth,
            )
        return
    if isinstance(payload, list):
        list_prefix = f"{prefix}[]" if prefix else "[]"
        if collect_only_ignored:
            ignored_keys.add(list_prefix)
        else:
            keys.add(list_prefix)
        for item in payload:
            _collect_schema_key_paths(
                item,
                keys=keys,
                ignored_keys=ignored_keys,
                collect_only_ignored=collect_only_ignored,
                prefix=list_prefix,
                depth=depth + 1,
                max_depth=max_depth,
            )


def _schema_fingerprint(
    payload: Any,
    *,
    key_counter: Optional[Counter[str]] = None,
    ignored_counter: Optional[Counter[str]] = None,
) -> Optional[str]:
    if not isinstance(payload, (dict, list)):
        return None
    keys: set[str] = set()
    ignored: set[str] = set()
    _collect_schema_key_paths(payload, keys=keys, ignored_keys=ignored)
    if key_counter is not None:
        for key in keys:
            key_counter[key] += 1
    if ignored_counter is not None:
        for key in ignored:
            ignored_counter[key] += 1
    canonical = "|".join(sorted(keys))
    return _fingerprint(canonical)


def _summarize_schema_key_stats(counter: Counter[str]) -> List[Dict[str, Any]]:
    return [
        {"path": path, "count": count}
        for path, count in counter.most_common(SCHEMA_KEY_STATS_LIMIT)
    ]


def _build_schema_key_stats(
    *,
    ticket_keys: Counter[str],
    ticket_ignored: Counter[str],
    shopify_keys: Counter[str],
    shopify_ignored: Counter[str],
) -> Dict[str, Any]:
    def _build_entry(
        keys_counter: Counter[str], ignored_counter: Counter[str]
    ) -> Dict[str, Any]:
        return {
            "filtered_total_unique": len(keys_counter),
            "ignored_total_unique": len(ignored_counter),
            "filtered_top_paths": _summarize_schema_key_stats(keys_counter),
            "ignored_top_paths": _summarize_schema_key_stats(ignored_counter),
        }

    return {
        "note": (
            "Key paths include field names only; schema drift excludes ids, timestamps, "
            "pagination, and volatile subtrees (ignored paths include nested keys)."
        ),
        "ticket": _build_entry(ticket_keys, ticket_ignored),
        "shopify": _build_entry(shopify_keys, shopify_ignored),
    }


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(round((pct / 100.0) * (len(sorted_values) - 1)))
    index = max(0, min(index, len(sorted_values) - 1))
    return sorted_values[index]


def _summarize_timing(
    ticket_durations: List[float], *, run_duration_seconds: float
) -> Dict[str, Any]:
    if not ticket_durations:
        return {
            "run_duration_seconds": round(run_duration_seconds, 3),
            "ticket_avg_seconds": 0.0,
            "ticket_p50_seconds": 0.0,
            "ticket_p95_seconds": 0.0,
            "ticket_min_seconds": 0.0,
            "ticket_max_seconds": 0.0,
        }
    avg = sum(ticket_durations) / len(ticket_durations)
    return {
        "run_duration_seconds": round(run_duration_seconds, 3),
        "ticket_avg_seconds": round(avg, 3),
        "ticket_p50_seconds": round(_percentile(ticket_durations, 50), 3),
        "ticket_p95_seconds": round(_percentile(ticket_durations, 95), 3),
        "ticket_min_seconds": round(min(ticket_durations), 3),
        "ticket_max_seconds": round(max(ticket_durations), 3),
    }


def _is_timeout_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "timeout" in text or "timed out" in text or "time out" in text


def _classify_status_code(prefix: str, status_code: Optional[int]) -> str:
    if status_code is None:
        return f"{prefix}_error"
    if status_code == 401:
        return f"{prefix}_401"
    if status_code == 403:
        return f"{prefix}_403"
    if status_code == 404:
        return f"{prefix}_404"
    if status_code == 429:
        return f"{prefix}_429"
    if 500 <= status_code < 600:
        return f"{prefix}_5xx"
    if 400 <= status_code < 500:
        return f"{prefix}_4xx"
    return f"{prefix}_status"


def _classify_richpanel_exception(exc: Exception) -> str:
    if isinstance(exc, SecretLoadError):
        return "richpanel_secret_load_error"
    if isinstance(exc, TransportError):
        if _is_timeout_error(exc):
            return "richpanel_timeout"
        return "richpanel_transport_error"
    if isinstance(exc, RichpanelRequestError):
        status = None
        response = getattr(exc, "response", None)
        if response is not None:
            status = getattr(response, "status_code", None)
        return _classify_status_code("richpanel", status)
    if _is_timeout_error(exc):
        return "richpanel_timeout"
    return "richpanel_error"


def _classify_shopify_exception(exc: Exception) -> str:
    if isinstance(exc, ShopifyTransportError):
        if _is_timeout_error(exc):
            return "shopify_timeout"
        return "shopify_transport_error"
    if isinstance(exc, ShopifyRequestError):
        status = None
        response = getattr(exc, "response", None)
        if response is not None:
            status = getattr(response, "status_code", None)
        if status is not None:
            return _classify_status_code("shopify", status)
        if _is_timeout_error(exc):
            return "shopify_timeout"
        return "shopify_error"
    if _is_timeout_error(exc):
        return "shopify_timeout"
    return "shopify_error"


def _map_order_resolution_reason(reason: str) -> Optional[str]:
    mapping = {
        "no_email_available": "no_customer_email",
        "shopify_no_match": "no_order_candidates",
        "email_only_multiple": "multiple_orders_ambiguous",
    }
    return mapping.get(reason)


def _extract_shopify_diagnostics_category(
    resolution: Dict[str, Any]
) -> Optional[str]:
    diagnostics = resolution.get("shopify_diagnostics")
    if not isinstance(diagnostics, dict):
        return None
    return _normalize_optional_text(diagnostics.get("category")) or None


def _classify_order_match_failure(result: Dict[str, Any]) -> Optional[str]:
    if result.get("order_matched"):
        return None
    resolution = result.get("order_resolution")
    if isinstance(resolution, dict):
        category = _extract_shopify_diagnostics_category(resolution)
        if category in {"auth_fail", "rate_limited", "http_error"}:
            return f"shopify_{category}"
        if category == "no_match":
            return "no_order_candidates"
        reason = _normalize_optional_text(resolution.get("reason"))
        mapped = _map_order_resolution_reason(reason)
        if mapped:
            return mapped
        if resolution.get("resolvedBy") == "no_match":
            return "no_order_candidates"
    if result.get("order_status_candidate") is False:
        return "no_order_status_candidate"
    return "order_match_failed"


def _extract_match_method(result: Dict[str, Any]) -> str:
    """
    Extract the match method used for order lookup.
    Returns one of: order_number, name_email, email_only, none, parse_error
    """
    if not result.get("order_matched"):
        return "none"
    
    resolution = result.get("order_resolution")
    if not isinstance(resolution, dict):
        return "none"
    
    resolved_by = _normalize_optional_text(resolution.get("resolvedBy"))
    
    # Map resolvedBy values to standard match methods
    if "order_number" in resolved_by:
        return "order_number"
    if "email_name" in resolved_by:
        return "name_email"
    if "email_only" in resolved_by:
        return "email_only"
    if resolved_by == "no_match":
        return "none"
    
    # If we have order_matched=True but no clear resolution, check for parse_error
    if result.get("failure_reason") == "parse_error":
        return "parse_error"
    
    # Default to none if we can't determine
    return "none"


def _extract_route_decision(result: Dict[str, Any]) -> str:
    """
    Extract the route decision (order_status vs non_order_status vs unknown).
    """
    routing = result.get("routing")
    if not isinstance(routing, dict):
        return "unknown"
    
    intent = _normalize_optional_text(routing.get("intent"))
    if not intent:
        return "unknown"
    
    # Normalize intent to order_status or non_order_status
    if intent in ("order_status", "order_tracking", "order_inquiry"):
        return "order_status"
    
    return "non_order_status"


def _classify_failure_reason_bucket(result: Dict[str, Any]) -> Optional[str]:
    """
    Classify failure into stable PII-safe buckets.
    Returns bucket name or None if no failure.
    """
    failure_reason = result.get("failure_reason")
    if not failure_reason:
        return None
    
    reason_str = str(failure_reason).lower()
    
    # Shopify API failures (including timeouts, HTTP status codes)
    if "shopify" in reason_str:
        return "shopify_api_error"
    
    # Richpanel API failures (including timeouts, HTTP status codes)
    if "richpanel" in reason_str:
        return "richpanel_api_error"
    
    # Match failures
    if "no_customer_email" in reason_str or "no_email" in reason_str:
        return "no_identifiers"
    if "no_order_candidates" in reason_str or "no_match" in reason_str:
        return "no_order_candidates"
    if "multiple_orders_ambiguous" in reason_str or "ambiguous" in reason_str:
        return "ambiguous_match"
    
    # Parse/data errors
    if "parse" in reason_str:
        return "parse_error"
    
    # Catch-all for other errors
    if "error" in reason_str:
        return "other_error"
    
    return "other_failure"


def _classify_match_failure_bucket(result: Dict[str, Any]) -> Optional[str]:
    """
    Classify match failures into PII-safe, reviewer-friendly buckets.
    Returns bucket name or None if no match failure.
    """
    if result.get("order_matched"):
        return None
    failure_reason = _normalize_optional_text(result.get("failure_reason")).lower()
    if not failure_reason:
        return "unknown"
    if "no_customer_email" in failure_reason or "no_email" in failure_reason:
        return "no_email"
    if "multiple_orders_ambiguous" in failure_reason or "ambiguous" in failure_reason:
        return "ambiguous_customer"
    if "no_order_candidates" in failure_reason:
        if not result.get("order_number_present"):
            return "no_order_number"
        return "no_order_candidates"
    if "no_order_status_candidate" in failure_reason or "order_match_failed" in failure_reason:
        if not result.get("order_number_present"):
            return "no_order_number"
        return "order_match_failed"
    if "parse" in failure_reason:
        return "parse_error"
    if "shopify" in failure_reason or "richpanel" in failure_reason:
        return "api_error"
    return "other_failure"


def _build_drift_watch(
    *,
    match_rate: float,
    api_error_rate: float,
    order_number_share: float,
    schema_new_ratio: float,
    ticket_fetch_failure_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    B61/C: Build drift watch section comparing current values to thresholds.
    Returns dict with current values, thresholds, and alert flags.
    """
    thresholds = DRIFT_THRESHOLDS
    
    # Convert rates to percentages for comparison
    match_rate_pct = match_rate * 100
    api_error_rate_pct = api_error_rate * 100
    order_number_share_pct = order_number_share * 100
    schema_new_ratio_pct = schema_new_ratio * 100
    ticket_fetch_failure_rate_pct = ticket_fetch_failure_rate * 100
    
    alerts = []
    
    # Note: For initial runs without historical data, we can't detect drops
    # We just report current values and thresholds
    
    # API error rate check (absolute)
    if api_error_rate_pct > thresholds["api_error_rate_pct"]:
        alerts.append({
            "metric": "api_error_rate",
            "threshold": thresholds["api_error_rate_pct"],
            "current": round(api_error_rate_pct, 2),
            "message": f"API error rate ({api_error_rate_pct:.1f}%) exceeds threshold ({thresholds['api_error_rate_pct']}%)"
        })
    
    # Schema drift check (absolute)
    if schema_new_ratio_pct > thresholds["schema_drift_new_ratio"] * 100:
        alerts.append({
            "metric": "schema_drift",
            "threshold": thresholds["schema_drift_new_ratio"] * 100,
            "current": round(schema_new_ratio_pct, 2),
            "message": f"Schema drift ({schema_new_ratio_pct:.1f}%) exceeds threshold ({thresholds['schema_drift_new_ratio'] * 100}%)"
        })
    
    return {
        "thresholds": thresholds,
        "current_values": {
            "match_rate_pct": round(match_rate_pct, 2),
            "api_error_rate_pct": round(api_error_rate_pct, 2),
            "order_number_share_pct": round(order_number_share_pct, 2),
            "schema_new_ratio_pct": round(schema_new_ratio_pct, 2),
            "ticket_fetch_failure_rate_pct": round(ticket_fetch_failure_rate_pct, 2),
        },
        "alerts": alerts,
        "has_alerts": len(alerts) > 0,
        "note": (
            "Historical comparison not yet implemented; schema drift uses filtered key paths "
            "(ids, timestamps, pagination, and volatile subtrees ignored)."
        ),
    }


def _build_drift_summary(
    *,
    ticket_total: int,
    ticket_new: int,
    ticket_unique: int,
    shopify_total: int,
    shopify_new: int,
    shopify_unique: int,
    threshold: float,
) -> Dict[str, Any]:
    ticket_ratio = ticket_new / ticket_total if ticket_total else 0.0
    shopify_ratio = shopify_new / shopify_total if shopify_total else 0.0
    warning = ticket_ratio > threshold or shopify_ratio > threshold
    return {
        "threshold": threshold,
        "warning": warning,
        "ticket_schema": {
            "total": ticket_total,
            "unique": ticket_unique,
            "new": ticket_new,
            "new_ratio": round(ticket_ratio, 4),
        },
        "shopify_schema": {
            "total": shopify_total,
            "unique": shopify_unique,
            "new": shopify_new,
            "new_ratio": round(shopify_ratio, 4),
        },
    }


def _compute_drift_watch(
    *,
    ticket_results: List[Dict[str, Any]],
    ticket_schema_total: int,
    ticket_schema_new: int,
    shopify_schema_total: int,
    shopify_schema_new: int,
) -> Dict[str, Any]:
    tickets_evaluated = len(ticket_results)
    match_rate = (
        sum(1 for result in ticket_results if result.get("order_matched"))
        / tickets_evaluated
        if tickets_evaluated
        else 0.0
    )
    api_errors = sum(
        1
        for result in ticket_results
        if result.get("failure_source") in ("richpanel_fetch", "shopify_fetch")
        and result.get("failure_reason") != "ticket_fetch_failed"
    )
    api_error_rate = api_errors / tickets_evaluated if tickets_evaluated else 0.0
    order_number_matches = sum(
        1 for result in ticket_results if _extract_match_method(result) == "order_number"
    )
    order_number_share = (
        order_number_matches / tickets_evaluated if tickets_evaluated else 0.0
    )
    ticket_fetch_failures = sum(
        1
        for result in ticket_results
        if result.get("failure_reason") == "ticket_fetch_failed"
    )
    ticket_fetch_failure_rate = (
        ticket_fetch_failures / tickets_evaluated if tickets_evaluated else 0.0
    )
    schema_new_ratio = max(
        ticket_schema_new / ticket_schema_total if ticket_schema_total else 0.0,
        shopify_schema_new / shopify_schema_total if shopify_schema_total else 0.0,
    )
    return _build_drift_watch(
        match_rate=match_rate,
        api_error_rate=api_error_rate,
        order_number_share=order_number_share,
        schema_new_ratio=schema_new_ratio,
        ticket_fetch_failure_rate=ticket_fetch_failure_rate,
    )


def _build_summary_payload(
    *,
    run_id: str,
    tickets_requested: int,
    ticket_results: List[Dict[str, Any]],
    timing: Dict[str, Any],
    drift: Dict[str, Any],
    schema_key_stats: Optional[Dict[str, Any]] = None,
    run_warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    tickets_evaluated = len(ticket_results)
    channel_counts = Counter(
        result.get("channel", "unknown") or "unknown" for result in ticket_results
    )
    order_match_success_count = sum(
        1 for result in ticket_results if result.get("order_matched")
    )
    order_match_failure_count = tickets_evaluated - order_match_success_count
    failure_reasons: Counter[str] = Counter()
    richpanel_fetch_failures: Counter[str] = Counter()
    shopify_fetch_failures: Counter[str] = Counter()
    
    # New B61/C metrics: route decisions, match methods, failure buckets
    route_decisions: Counter[str] = Counter()
    match_methods: Counter[str] = Counter()
    failure_buckets: Counter[str] = Counter()
    match_failure_buckets: Counter[str] = Counter()
    tracking_or_eta_available_count = 0
    would_reply_send = False
    
    for result in ticket_results:
        # Existing failure tracking
        reason = result.get("failure_reason")
        source = result.get("failure_source")
        if reason:
            failure_reasons[str(reason)] += 1
            if source == "richpanel_fetch":
                richpanel_fetch_failures[str(reason)] += 1
            if source == "shopify_fetch":
                shopify_fetch_failures[str(reason)] += 1
        
        # New: route decision distribution
        route_decision = _extract_route_decision(result)
        route_decisions[route_decision] += 1
        
        # New: match method telemetry
        match_method = _extract_match_method(result)
        match_methods[match_method] += 1
        
        # New: failure reason bucketing
        failure_bucket = _classify_failure_reason_bucket(result)
        if failure_bucket:
            failure_buckets[failure_bucket] += 1

        # New: match failure bucket with reviewer-friendly labels
        match_failure_bucket = _classify_match_failure_bucket(result)
        if match_failure_bucket:
            match_failure_buckets[match_failure_bucket] += 1

        # Tracking/ETA availability
        if result.get("tracking_found") or result.get("eta_available"):
            tracking_or_eta_available_count += 1

        if result.get("would_reply_send"):
            would_reply_send = True
    
    top_failure_reasons = [
        {"reason": reason, "count": count}
        for reason, count in sorted(
            failure_reasons.items(), key=lambda item: (-item[1], item[0])
        )[:SUMMARY_TOP_FAILURE_REASONS]
    ]
    success_rate = (
        order_match_success_count / tickets_evaluated if tickets_evaluated else 0.0
    )
    tracking_or_eta_rate = (
        tracking_or_eta_available_count / tickets_evaluated if tickets_evaluated else 0.0
    )
    
    # Calculate percentages for new metrics
    route_decision_pcts = {
        decision: round(count / tickets_evaluated, 4) if tickets_evaluated else 0.0
        for decision, count in route_decisions.items()
    }
    match_method_pcts = {
        method: round(count / tickets_evaluated, 4) if tickets_evaluated else 0.0
        for method, count in match_methods.items()
    }
    match_failure_payload: Dict[str, int] = {
        key: match_failure_buckets.get(key, 0) for key in MATCH_FAILURE_BUCKET_KEYS
    }
    for bucket, count in match_failure_buckets.items():
        if bucket not in match_failure_payload:
            match_failure_payload[bucket] = count
    
    warnings = sorted({str(item) for item in (run_warnings or []) if item})
    payload = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_size_requested": tickets_requested,
        "ticket_count": tickets_evaluated,
        "tickets_evaluated": tickets_evaluated,
        "email_channel_count": channel_counts.get("email", 0),
        "chat_channel_count": channel_counts.get("chat", 0),
        "unknown_channel_count": channel_counts.get("unknown", 0),
        "order_match_success_count": order_match_success_count,
        "order_match_failure_count": order_match_failure_count,
        "order_match_success_rate": round(success_rate, 4),
        "match_success_rate": round(success_rate, 4),
        "tracking_or_eta_available_count": tracking_or_eta_available_count,
        "tracking_or_eta_available_rate": round(tracking_or_eta_rate, 4),
        "would_reply_send": bool(would_reply_send),
        # B61/C: Route decision distribution
        "route_decisions": dict(route_decisions),
        "route_decision_percentages": route_decision_pcts,
        # B61/C: Match method telemetry
        "match_methods": dict(match_methods),
        "match_method_percentages": match_method_pcts,
        # B61/C: Failure buckets (PII-safe categorization)
        "failure_buckets": dict(failure_buckets),
        "match_failure_buckets": match_failure_payload,
        "top_failure_reasons": top_failure_reasons,
        "failure_reasons": dict(failure_reasons),
        "richpanel_fetch_failures": dict(richpanel_fetch_failures),
        "shopify_fetch_failures": dict(shopify_fetch_failures),
        "timing": timing,
        "schema_drift": drift,
        "run_warnings": warnings,
        "status": "warning" if drift.get("warning") else "ok",
    }
    if schema_key_stats:
        payload["schema_key_stats"] = schema_key_stats
    return payload


def _resolve_env_name() -> str:
    raw = (
        os.environ.get("RICHPANEL_ENV")
        or os.environ.get("RICH_PANEL_ENV")
        or os.environ.get("MW_ENV")
        or os.environ.get("ENVIRONMENT")
        or "local"
    )
    return str(raw).strip().lower() or "local"


def _require_prod_environment(*, allow_non_prod: bool) -> str:
    env_name = _resolve_env_name()
    if env_name in ALLOWED_PROD_ENVS:
        return env_name
    if allow_non_prod:
        return env_name
    raise SystemExit(
        "ENVIRONMENT must resolve to prod for live read-only eval "
        "(use --allow-non-prod for local tests)"
    )


def _resolve_richpanel_base_url() -> str:
    return (os.environ.get("RICHPANEL_API_BASE_URL") or PROD_RICHPANEL_BASE_URL).rstrip("/")


def _require_env_flag(key: str, expected: str, *, context: str) -> None:
    actual = os.environ.get(key)
    if actual is None:
        raise SystemExit(f"{key} must be {expected} for {context} (unset)")
    if str(actual).strip().lower() != expected:
        raise SystemExit(f"{key} must be {expected} for {context} (found {actual})")


def _require_env_flags(context: str) -> Dict[str, str]:
    """Require the read-only env settings (fail-closed; do not mutate env)."""
    applied: Dict[str, str] = {}
    for key, expected in REQUIRED_FLAGS.items():
        _require_env_flag(key, expected, context=context)
        applied[key] = expected
    return applied


def _build_richpanel_client(
    *, richpanel_secret: Optional[str], base_url: str
) -> RichpanelClient:
    return RichpanelClient(
        api_key_secret_id=richpanel_secret,
        base_url=base_url,
        dry_run=False,  # allow GETs; writes are still blocked by read-only + env guard
        read_only=True,
    )


def _build_shopify_client(
    *,
    allow_network: Optional[bool],
    shop_domain: Optional[str],
    secrets_client: Optional[Any] = None,
) -> ShopifyClient:
    return ShopifyClient(
        shop_domain=shop_domain,
        allow_network=allow_network,
        secrets_client=secrets_client,
    )


def _resolve_shopify_secrets_client() -> Optional[Any]:
    profile = os.environ.get("SHOPIFY_ACCESS_TOKEN_PROFILE")
    if not profile:
        return None
    if boto3 is None:
        raise SystemExit("boto3 is required for SHOPIFY_ACCESS_TOKEN_PROFILE usage")
    region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-2"
    )
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client("secretsmanager", region_name=region)


def _probe_shopify(
    *, shop_domain: Optional[str], secrets_client: Optional[Any] = None
) -> Dict[str, Any]:
    client = _build_shopify_client(
        allow_network=None,
        shop_domain=shop_domain,
        secrets_client=secrets_client,
    )
    response = client.request(
        "GET",
        "orders/count.json",
        params={"status": "any"},
        dry_run=False,
        safe_mode=False,
        automation_enabled=True,
    )
    ok = response.status_code < 400 and not response.dry_run
    return {"status_code": response.status_code, "dry_run": response.dry_run, "ok": ok}


def _is_prod_target(*, richpanel_base_url: str, richpanel_secret_id: Optional[str]) -> bool:
    env_name = _resolve_env_name()
    if env_name in {"prod", "production"}:
        return True
    if richpanel_secret_id and "/prod/" in richpanel_secret_id.lower():
        return True
    prod_key_present = bool(
        os.environ.get("PROD_RICHPANEL_API_KEY")
        or os.environ.get("RICHPANEL_API_KEY_OVERRIDE")
    )
    is_prod_base = richpanel_base_url.rstrip("/") == PROD_RICHPANEL_BASE_URL
    return prod_key_present and is_prod_base


def _redact_path(path: str) -> str:
    if not path:
        return "/"
    segments = [segment for segment in path.split("/") if segment]
    safe_segments = {
        "api",
        "v1",
        "v2",
        "v3",
        "tickets",
        "ticket",
        "conversations",
        "conversation",
        "orders",
        "order",
        "number",
        "shipments",
        "shipment",
    }
    redacted_segments: list[str] = []
    for segment in segments:
        lowered = segment.lower()
        if lowered in safe_segments or (segment.startswith("v") and segment[1:].isdigit()):
            redacted_segments.append(segment)
            continue
        if segment.isalpha() and len(segment) <= 32:
            redacted_segments.append(segment)
            continue
        redacted_segments.append(_redact_identifier(segment) or "redacted")
    return "/" + "/".join(redacted_segments)


def _service_from_hostname(hostname: str) -> str:
    if not hostname:
        return "unknown"
    if hostname.endswith("richpanel.com"):
        return "richpanel"
    if hostname.endswith("myshopify.com"):
        return "shopify"
    if hostname.endswith("shipstation.com"):
        return "shipstation"
    if hostname.endswith("openai.com"):
        return "openai"
    if hostname.endswith("anthropic.com"):
        return "anthropic"
    if hostname.endswith("amazonaws.com"):
        prefix = hostname.split(".")[0].strip().lower()
        return f"aws_{prefix}" if prefix else "aws"
    return "unknown"


AWS_ALLOWED_OPERATIONS = {
    "AssumeRole",
    "AssumeRoleWithSAML",
    "AssumeRoleWithWebIdentity",
    "GetAccessKeyInfo",
    "GetCallerIdentity",
    "GetRoleCredentials",
    "GetSecretValue",
    "GetSessionToken",
}


def _extract_aws_operation(request: Any) -> Optional[str]:
    context = getattr(request, "context", None)
    if isinstance(context, dict):
        for key in ("operation_name", "operation"):
            value = context.get(key)
            if value:
                return str(value)

    headers = getattr(request, "headers", None) or {}
    target = None
    if isinstance(headers, dict):
        target = headers.get("X-Amz-Target") or headers.get("x-amz-target")
    else:
        getter = getattr(headers, "get", None)
        if callable(getter):
            target = getter("X-Amz-Target") or getter("x-amz-target")
    if target:
        operation = str(target).split(".")[-1]
        return operation.strip().strip("'\"")

    body = getattr(request, "body", None)
    if body is None:
        body = getattr(request, "data", None)
    if body:
        if isinstance(body, (bytes, bytearray)):
            text = body.decode("utf-8", errors="ignore")
        else:
            text = str(body)
        parsed = urllib.parse.parse_qs(text, keep_blank_values=True)
        for key in ("Action", "action"):
            action = parsed.get(key)
            if action:
                return str(action[0]).strip().strip("'\"")
    return None


class _AwsSdkTrace:
    def __init__(self, entries: List[Dict[str, str]]) -> None:
        self.entries = entries
        self._original_send = None
        self.enabled = False
        self.error: Optional[str] = None

    def capture(self) -> None:
        if self._original_send is not None:
            return
        try:
            import botocore.endpoint  # type: ignore
        except Exception:
            self.enabled = False
            self.error = "botocore_unavailable"
            return

        self._original_send = botocore.endpoint.Endpoint._send
        self.enabled = True

        def _wrapped_send(endpoint, request):
            try:
                method = getattr(request, "method", "GET")
                url = getattr(request, "url", "")
                operation = _extract_aws_operation(request)
                parsed = urllib.parse.urlparse(url)
                entry = {
                    "method": str(method).upper(),
                    "path": _redact_path(parsed.path),
                    "service": _service_from_hostname(parsed.hostname or ""),
                    "source": "aws_sdk",
                }
                if operation:
                    entry["operation"] = operation
                self.entries.append(entry)
            except Exception:
                LOGGER.warning("AWS SDK trace capture failed", exc_info=True)
            return self._original_send(endpoint, request)

        botocore.endpoint.Endpoint._send = _wrapped_send

    def stop(self) -> None:
        if self._original_send is not None:
            try:
                import botocore.endpoint  # type: ignore
            except Exception:
                pass
            else:
                botocore.endpoint.Endpoint._send = self._original_send
            self._original_send = None


class _HttpTrace:
    _original_urlopen: Any

    def __init__(self) -> None:
        self.entries: list[Dict[str, str]] = []
        self._original_urlopen = None
        self._aws_trace = _AwsSdkTrace(self.entries)

    def record(self, method: str, url: str, *, source: str = "urllib") -> None:
        parsed = urllib.parse.urlparse(url)
        path = _redact_path(parsed.path)
        service = _service_from_hostname(parsed.hostname or "")
        self.entries.append(
            {
                "method": method.upper(),
                "path": path,
                "service": service,
                "source": source,
            }
        )

    def capture(self) -> "_HttpTrace":
        original = urllib.request.urlopen
        self._original_urlopen = original  # type: ignore

        def _wrapped_urlopen(req, *args, **kwargs):
            try:
                method = (
                    req.get_method() if hasattr(req, "get_method") else "GET"
                )
                url = req.full_url if hasattr(req, "full_url") else str(req)
                self.record(method, url)
            except Exception:
                LOGGER.warning("HTTP trace capture failed", exc_info=True)
            return original(req, *args, **kwargs)

        urllib.request.urlopen = _wrapped_urlopen  # type: ignore
        self._aws_trace.capture()
        return self

    def stop(self) -> None:
        if self._original_urlopen is not None:
            urllib.request.urlopen = self._original_urlopen  # type: ignore
            self._original_urlopen = None
        self._aws_trace.stop()

    def assert_read_only(self, *, allow_openai: bool, trace_path: Path) -> None:
        allowed = {
            "richpanel": {"GET", "HEAD"},
            "shopify": {"GET", "HEAD"},
            "shipstation": {"GET", "HEAD"},
            "openai": {"POST"},
            "anthropic": {"POST"},
        }
        violations = []
        for entry in self.entries:
            service = entry["service"]
            method = entry["method"]
            if service.startswith("aws"):
                normalized = service.lower()
                if any(token in normalized for token in ("oidc", "sso", "portal")):
                    if method not in {"GET", "POST"}:
                        violations.append(entry)
                    continue
                operation = entry.get("operation")
                if method != "POST":
                    violations.append(entry)
                    continue
                if not operation or operation not in AWS_ALLOWED_OPERATIONS:
                    violations.append(entry)
                continue
            if service in {"openai", "anthropic"} and not allow_openai:
                violations.append(entry)
                continue
            if service not in allowed:
                violations.append(entry)
                continue
            if method not in allowed[service]:
                violations.append(entry)

        if violations:
            raise SystemExit(
                f"Non-read-only HTTP request detected. Trace: {trace_path}"
            )

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": list(self.entries),
            "aws_sdk_trace_enabled": self._aws_trace.enabled,
        }
        if self._aws_trace.error:
            payload["aws_sdk_trace_error"] = self._aws_trace.error
        payload["note"] = (
            "Captured via urllib.request.urlopen and botocore Endpoint._send "
            "(AWS SDK); entries include source and optional aws operation."
        )
        return payload


def _summarize_trace(trace: _HttpTrace, *, allow_openai: bool) -> Dict[str, Any]:
    methods = Counter(entry.get("method") for entry in trace.entries)
    services = Counter(entry.get("service") for entry in trace.entries)
    sources = Counter(entry.get("source") for entry in trace.entries)
    aws_operations = Counter(
        entry.get("operation")
        for entry in trace.entries
        if entry.get("service", "").startswith("aws") and entry.get("operation")
    )
    allowed = {
        "richpanel": {"GET", "HEAD"},
        "shopify": {"GET", "HEAD"},
        "shipstation": {"GET", "HEAD"},
        "openai": {"POST"},
        "anthropic": {"POST"},
    }
    aws_missing_ops = 0
    allowed_methods_only = True
    for entry in trace.entries:
        service = entry.get("service")
        method = entry.get("method")
        if service and str(service).startswith("aws"):
            normalized = str(service).lower()
            if any(token in normalized for token in ("oidc", "sso", "portal")):
                if method not in {"GET", "POST"}:
                    allowed_methods_only = False
                    break
                continue
            if method != "POST":
                allowed_methods_only = False
                break
            operation = entry.get("operation")
            if not operation or operation not in AWS_ALLOWED_OPERATIONS:
                aws_missing_ops += 1
                allowed_methods_only = False
                break
            continue
        if service in {"openai", "anthropic"} and not allow_openai:
            allowed_methods_only = False
            break
        if service not in allowed:
            allowed_methods_only = False
            break
        if method not in allowed[service]:
            allowed_methods_only = False
            break
    return {
        "total_requests": len(trace.entries),
        "methods": dict(methods),
        "services": dict(services),
        "sources": dict(sources),
        "aws_operations": dict(aws_operations),
        "aws_missing_operations": aws_missing_ops,
        "aws_sdk_trace_enabled": trace._aws_trace.enabled,
        "allowed_methods_only": allowed_methods_only,
    }



def _fetch_ticket(client: RichpanelClient, ticket_ref: str) -> Dict[str, Any]:
    """Fetch ticket by id or ticket number; return payload + metadata."""
    encoded = urllib.parse.quote(ticket_ref, safe="")
    attempts = (
        f"/v1/tickets/{encoded}",
        f"/v1/tickets/number/{encoded}",
    )
    errors: list[str] = []
    for path in attempts:
        try:
            resp = client.request("GET", path, dry_run=False, log_body_excerpt=False)
        except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
            errors.append(f"{_redact_path(path)}: {exc.__class__.__name__}")
            continue
        if resp.dry_run or resp.status_code >= 400:
            errors.append(
                f"{_redact_path(path)}: status {resp.status_code} dry_run={resp.dry_run}"
            )
            continue

        payload = resp.json() or {}
        if isinstance(payload, dict) and isinstance(payload.get("ticket"), dict):
            payload = payload["ticket"]
        payload = payload if isinstance(payload, dict) else {}
        payload["__source_path"] = _redact_path(path)
        return payload
    redacted_ref = _redact_identifier(ticket_ref) or "redacted"
    raise SystemExit(
        f"Ticket lookup failed for {redacted_ref}: {'; '.join(errors)}"
    )


def _fetch_conversation(
    client: RichpanelClient,
    ticket_id: str,
    *,
    conversation_id: Optional[str] = None,
    conversation_no: Optional[object] = None,
) -> Dict[str, Any]:
    """Best-effort conversation read; tolerates failures."""
    candidates: list[str] = []
    for value in (conversation_id, conversation_no, ticket_id):
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in candidates:
            candidates.append(text)

    attempts = (
        "/api/v1/conversations/{encoded}",
        "/v1/conversations/{encoded}",
        "/api/v1/conversations/{encoded}/messages",
        "/v1/conversations/{encoded}/messages",
    )

    for candidate in candidates:
        encoded = urllib.parse.quote(candidate, safe="")
        for template in attempts:
            path = template.format(encoded=encoded)
            try:
                resp = client.request(
                    "GET",
                    path,
                    dry_run=False,
                    log_body_excerpt=False,
                )
            except Exception:
                LOGGER.warning(
                    "Conversation fetch failed for %s", _redact_path(path)
                )
                continue
            if resp.dry_run or resp.status_code >= 400:
                LOGGER.warning(
                    "Conversation fetch skipped for %s status=%s dry_run=%s",
                    _redact_path(path),
                    resp.status_code,
                    resp.dry_run,
                )
                continue
            try:
                payload = resp.json()
            except Exception:
                LOGGER.warning(
                    "Conversation parse failed for %s", _redact_path(path)
                )
                continue
            if isinstance(payload, list):
                payload = {"messages": payload}
            if isinstance(payload, dict) and isinstance(payload.get("conversation"), dict):
                convo = dict(payload.get("conversation") or {})
                if isinstance(payload.get("messages"), list) and "messages" not in convo:
                    convo["messages"] = payload["messages"]
                payload = convo
            payload = payload if isinstance(payload, dict) else {}
            if payload:
                payload["__source_path"] = _redact_path(path)
                return payload
    return {}


def _extract_latest_customer_message(
    ticket: Dict[str, Any], convo: Dict[str, Any]
) -> str:
    text = extract_customer_message(ticket, default="")
    if text:
        return text
    text = _extract_comment_message(ticket, extractor=extract_customer_message)
    if text:
        return text
    text = extract_customer_message(convo, default="")
    if text:
        return text
    text = _extract_comment_message(convo, extractor=extract_customer_message)
    if text:
        return text
    messages = convo.get("messages") or convo.get("conversation_messages") or []
    if isinstance(messages, list):
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            sender = str(
                message.get("sender_type") or message.get("author_type") or ""
            ).strip().lower()
            if sender not in {"customer", "user", "end_user", "shopper"}:
                continue
            candidate = extract_customer_message(message, default="")
            if candidate:
                return candidate
    return ""


def _extract_order_payload(ticket: Dict[str, Any], convo: Dict[str, Any]) -> Dict[str, Any]:
    """Blend known order fields to feed the pipeline order lookup."""
    candidates: list[Dict[str, Any]] = []
    for source in (ticket, convo):
        if isinstance(source, dict):
            candidates.append(source)
            order = source.get("order")
            if isinstance(order, dict):
                candidates.append(order)
            orders = source.get("orders")
            if isinstance(orders, list) and orders and isinstance(orders[0], dict):
                candidates.append(orders[0])

    merged: Dict[str, Any] = {}
    for data in candidates:
        for key, val in data.items():
            if key in ("__source_path",):
                continue
            merged.setdefault(key, val)
    if not merged.get("order_number") and not merged.get("orderNumber"):
        order_number = extract_order_number(ticket) or extract_order_number(convo)
        if order_number:
            merged["order_number"] = order_number
    return merged


def _tracking_present(order_summary: Dict[str, Any]) -> bool:
    if not isinstance(order_summary, dict):
        return False
    for key in (
        "tracking_number",
        "tracking",
        "tracking_no",
        "trackingCode",
        "tracking_url",
        "trackingUrl",
        "tracking_link",
        "status_url",
        "carrier",
        "shipping_carrier",
        "carrier_name",
        "carrierName",
    ):
        value = order_summary.get(key)
        if value not in (None, "", [], {}):
            return True
    return False


def _delivery_estimate_present(delivery_estimate: Any) -> bool:
    if not isinstance(delivery_estimate, dict):
        return False
    for key in ("eta_human", "window_min_days", "window_max_days", "bucket", "is_late"):
        value = delivery_estimate.get(key)
        if value not in (None, "", [], {}):
            return True
    return False


def _redact_tracking_number(tracking: Optional[str]) -> Optional[str]:
    """Redact tracking number for PII safety.
    
    For security, always show minimal chars:
    - Empty/whitespace-only: return None
    - Length <= 6: show "***" only (too short to safely expose any chars)
    - Length 7-10: show first 2 + last 2 chars
    - Length > 10: show first 4 + last 3 chars
    """
    if not tracking or not isinstance(tracking, str):
        return None
    tracking = tracking.strip()
    if not tracking:  # Handle whitespace-only strings consistently with empty strings
        return None
    if len(tracking) <= 6:
        return "***"
    if len(tracking) <= 10:
        return f"{tracking[:2]}***{tracking[-2:]}"
    return f"{tracking[:4]}***{tracking[-3:]}"


def _redact_date(date_str: Optional[str]) -> Optional[str]:
    """Redact date for PII safety: show year-month only."""
    if not date_str or not isinstance(date_str, str):
        return None
    # Extract just YYYY-MM from ISO date
    parts = date_str.split("T")[0].split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}-XX"
    return "XXXX-XX-XX"


def _compute_eta_for_ticket(
    order_summary: Dict[str, Any],
    ticket_created_at: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Compute ETA for a ticket using order date + shipping method + ticket date.
    Returns a PII-safe summary of the ETA calculation.
    """
    order_created = (
        order_summary.get("created_at")
        or order_summary.get("order_created_at")
    )
    shipping_method = (
        order_summary.get("shipping_method")
        or order_summary.get("shipping_method_name")
    )
    inquiry_date = ticket_created_at or datetime.now(timezone.utc).isoformat()

    if not order_created or not shipping_method:
        return None

    estimate = compute_delivery_estimate(order_created, shipping_method, inquiry_date)
    if not estimate:
        return None

    return {
        "order_date_redacted": _redact_date(estimate.get("order_created_date")),
        "inquiry_date_redacted": _redact_date(estimate.get("inquiry_date")),
        "shipping_method": estimate.get("normalized_method") or estimate.get("raw_method"),
        "elapsed_business_days": estimate.get("elapsed_business_days"),
        "remaining_min_days": estimate.get("remaining_min_days"),
        "remaining_max_days": estimate.get("remaining_max_days"),
        "eta_human": estimate.get("eta_human"),
        "is_late": estimate.get("is_late"),
        "bucket": estimate.get("bucket"),
    }


def _order_context_summary(
    order_payload: Dict[str, Any],
    order_summary: Optional[Dict[str, Any]],
    *,
    conversation_id: str,
) -> Dict[str, Any]:
    envelope_stub = SimpleNamespace(conversation_id=conversation_id)
    missing_fields = _missing_order_context(
        order_summary or {}, envelope_stub, order_payload
    )
    order_number_present = bool(
        order_payload.get("order_number") or order_payload.get("orderNumber")
    )
    tracking_or_shipping_method_present = not any(
        field in missing_fields
        for field in ("tracking_or_shipping_method", "shipping_method_bucket")
    )
    return {
        "order_id_present": "order_id" not in missing_fields,
        "order_number_present": order_number_present,
        "order_created_at_present": "created_at" not in missing_fields,
        "tracking_or_shipping_method_present": tracking_or_shipping_method_present,
        "order_context_missing": missing_fields,
    }


def _build_run_id() -> str:
    return datetime.now(timezone.utc).strftime("RUN_%Y%m%d_%H%MZ")


def _build_artifact_dir() -> Path:
    out_dir = ROOT / "artifacts" / "readonly_shadow"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _build_report_paths(run_id: str) -> Tuple[Path, Path, Path]:
    out_dir = _build_artifact_dir()
    json_path = out_dir / f"live_readonly_shadow_eval_report_{run_id}.json"
    md_path = out_dir / f"live_readonly_shadow_eval_report_{run_id}.md"
    trace_path = out_dir / f"live_readonly_shadow_eval_http_trace_{run_id}.json"
    return json_path, md_path, trace_path


def _resolve_report_path(out_path: str) -> Path:
    candidate = Path(out_path)
    if candidate.suffix.lower() == ".json":
        return candidate
    if candidate.exists() and candidate.is_dir():
        return candidate / CUSTOM_REPORT_FILENAME
    if str(out_path).endswith(("/", "\\")):
        return candidate / CUSTOM_REPORT_FILENAME
    return candidate.with_suffix(".json")


def _resolve_output_paths(
    run_id: str,
    *,
    out_path: Optional[str],
    summary_md_out: Optional[str],
) -> Tuple[Path, Path, Path, Path]:
    if out_path:
        report_path = _resolve_report_path(out_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path = report_path.parent / CUSTOM_SUMMARY_JSON_FILENAME
        trace_path = report_path.parent / CUSTOM_TRACE_FILENAME
        if summary_md_out:
            report_md_path = Path(summary_md_out)
        else:
            report_md_path = report_path.parent / CUSTOM_SUMMARY_MD_FILENAME
        report_md_path.parent.mkdir(parents=True, exist_ok=True)
        return report_path, summary_path, report_md_path, trace_path

    report_path, report_md_path, trace_path = _build_report_paths(run_id)
    if summary_md_out:
        report_md_path = Path(summary_md_out)
        report_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = report_path.parent / f"live_readonly_shadow_eval_summary_{run_id}.json"
    return report_path, summary_path, report_md_path, trace_path


def _build_markdown_report(
    report: Dict[str, Any], summary_payload: Dict[str, Any]
) -> List[str]:
    counts = report.get("counts", {})
    target = report.get("target", {})
    shopify_probe = report.get("shopify_probe", {})
    trace_summary = report.get("http_trace_summary", {})

    run_id = report.get("run_id", "RUN_UNKNOWN")
    timestamp = report.get("timestamp", "")
    env_name = report.get("environment", "unknown")
    sample_mode = report.get("sample_mode", "unknown")
    summary_path = report.get("summary_path", "n/a")
    trace_path = report.get("http_trace_path", "n/a")

    route_decisions = summary_payload.get("route_decisions", {})
    route_pcts = summary_payload.get("route_decision_percentages", {})
    match_methods = summary_payload.get("match_methods", {})
    match_pcts = summary_payload.get("match_method_percentages", {})
    failure_buckets = summary_payload.get("failure_buckets", {})
    match_failure_buckets = summary_payload.get("match_failure_buckets", {})
    drift_watch = summary_payload.get("drift_watch", {})
    drift_warning = summary_payload.get("schema_drift", {}).get("warning", False)
    run_warnings = summary_payload.get("run_warnings", [])

    md_lines = [
        "# Live Read-Only Shadow Eval Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Generated (UTC): {timestamp}",
        f"- Environment: `{env_name}`",
        f"- Region: `{target.get('region') or 'n/a'}`",
        f"- Stack name: `{target.get('stack_name') or 'n/a'}`",
        f"- Sample mode: `{sample_mode}`",
        f"- Tickets requested: {counts.get('tickets_requested', 0)}",
        f"- Tickets scanned: {counts.get('tickets_scanned', 0)}",
        f"- Orders matched: {counts.get('orders_matched', 0)}",
        f"- Tracking found: {counts.get('tracking_found', 0)}",
        f"- ETA available: {counts.get('eta_available', 0)}",
        f"- Tracking or ETA available: {counts.get('tracking_or_eta_available', 0)}",
        f"- Match success rate: {summary_payload.get('match_success_rate', 0) * 100:.1f}%",
        f"- Would reply send: {summary_payload.get('would_reply_send', False)}",
        f"- Errors: {counts.get('errors', 0)}",
        f"- Shopify probe enabled: {shopify_probe.get('enabled')}",
        f"- Shopify probe ok: {shopify_probe.get('ok')}",
        f"- Shopify probe status: {shopify_probe.get('status_code')}",
        f"- Summary path: `{summary_path}`",
        f"- Drift warning: {drift_warning}",
        f"- Run warnings: {', '.join(run_warnings) or 'none'}",
        "",
        "## Route Decision Distribution (B61/C)",
        f"- Order Status: {route_decisions.get('order_status', 0)} ({route_pcts.get('order_status', 0) * 100:.1f}%)",
        f"- Non-Order Status: {route_decisions.get('non_order_status', 0)} ({route_pcts.get('non_order_status', 0) * 100:.1f}%)",
        f"- Unknown: {route_decisions.get('unknown', 0)} ({route_pcts.get('unknown', 0) * 100:.1f}%)",
        "",
        "## Match Method Telemetry (B61/C)",
        f"- Order Number: {match_methods.get('order_number', 0)} ({match_pcts.get('order_number', 0) * 100:.1f}%)",
        f"- Name + Email: {match_methods.get('name_email', 0)} ({match_pcts.get('name_email', 0) * 100:.1f}%)",
        f"- Email Only: {match_methods.get('email_only', 0)} ({match_pcts.get('email_only', 0) * 100:.1f}%)",
        f"- No Match: {match_methods.get('none', 0)} ({match_pcts.get('none', 0) * 100:.1f}%)",
        f"- Parse Error: {match_methods.get('parse_error', 0)} ({match_pcts.get('parse_error', 0) * 100:.1f}%)",
        "",
        "## Failure Buckets (B61/C - PII Safe)",
        f"- No Identifiers: {failure_buckets.get('no_identifiers', 0)}",
        f"- Shopify API Error: {failure_buckets.get('shopify_api_error', 0)}",
        f"- Richpanel API Error: {failure_buckets.get('richpanel_api_error', 0)}",
        f"- Ambiguous Match: {failure_buckets.get('ambiguous_match', 0)}",
        f"- No Order Candidates: {failure_buckets.get('no_order_candidates', 0)}",
        f"- Parse Error: {failure_buckets.get('parse_error', 0)}",
        f"- Other Errors: {failure_buckets.get('other_error', 0) + failure_buckets.get('other_failure', 0)}",
        "",
        "## Match Failure Buckets (Deployment Gate)",
        f"- No Email: {match_failure_buckets.get('no_email', 0)}",
        f"- No Order Number: {match_failure_buckets.get('no_order_number', 0)}",
        f"- Ambiguous Customer: {match_failure_buckets.get('ambiguous_customer', 0)}",
        f"- No Order Candidates: {match_failure_buckets.get('no_order_candidates', 0)}",
        f"- Order Match Failed: {match_failure_buckets.get('order_match_failed', 0)}",
        f"- Parse Error: {match_failure_buckets.get('parse_error', 0)}",
        f"- API Error: {match_failure_buckets.get('api_error', 0)}",
        f"- Other/Unknown: {match_failure_buckets.get('other_failure', 0) + match_failure_buckets.get('unknown', 0)}",
        "",
        "## Drift Watch (B61/C)",
        f"- Match Rate: {drift_watch.get('current_values', {}).get('match_rate_pct', 0):.1f}% (threshold: drop > {DRIFT_THRESHOLDS['match_rate_drop_pct']}%)",
        f"- API Error Rate: {drift_watch.get('current_values', {}).get('api_error_rate_pct', 0):.1f}% (threshold: > {DRIFT_THRESHOLDS['api_error_rate_pct']}%)",
        f"- Ticket Fetch Failure Rate: {drift_watch.get('current_values', {}).get('ticket_fetch_failure_rate_pct', 0):.1f}% (warning-only)",
        f"- Order Number Share: {drift_watch.get('current_values', {}).get('order_number_share_pct', 0):.1f}% (threshold: drop > {DRIFT_THRESHOLDS['order_number_share_drop_pct']}%)",
        f"- Schema Drift: {drift_watch.get('current_values', {}).get('schema_new_ratio_pct', 0):.1f}% (threshold: > {DRIFT_THRESHOLDS['schema_drift_new_ratio'] * 100}%)",
        f"- **Alerts: {len(drift_watch.get('alerts', []))}**",
    ]

    for alert in drift_watch.get("alerts", []):
        md_lines.append(f"  - ⚠️ {alert.get('message', 'Unknown alert')}")

    md_lines.extend(
        [
            "",
            "## HTTP Trace Summary",
            f"- Total requests: {trace_summary.get('total_requests', 0)}",
            f"- Methods: {json.dumps(trace_summary.get('methods', {}), sort_keys=True)}",
            f"- Services: {json.dumps(trace_summary.get('services', {}), sort_keys=True)}",
            f"- Sources: {json.dumps(trace_summary.get('sources', {}), sort_keys=True)}",
            f"- AWS operations: {json.dumps(trace_summary.get('aws_operations', {}), sort_keys=True)}",
            f"- AWS missing operations: {trace_summary.get('aws_missing_operations', 0)}",
            f"- Allowed methods only: {trace_summary.get('allowed_methods_only', False)}",
            f"- Trace path: `{trace_path}`",
            "",
        ]
    )
    request_burst = report.get("richpanel_request_burst") or {}
    if request_burst:
        md_lines.extend(
            [
                "## Richpanel Burst Summary (30s)",
                (
                    f"- Max requests in any 30s window: "
                    f"{request_burst.get('max_requests_overall', 0)}"
                ),
                "",
            ]
        )
    retry_after_validation = report.get("richpanel_retry_after_validation") or {}
    if retry_after_validation:
        md_lines.extend(
            [
                "## Retry-After Validation",
                (
                    f"- Checked: {retry_after_validation.get('checked', 0)}; "
                    f"violations: {retry_after_validation.get('violations', 0)}"
                ),
                "",
            ]
        )
    identity = report.get("richpanel_identity") or {}
    if identity:
        md_lines.extend(
            [
                "## Richpanel Identity",
                f"- base_url: {identity.get('richpanel_base_url')}",
                f"- resolved_env: {identity.get('resolved_env')}",
                f"- api_key_hash: {identity.get('api_key_hash')}",
                f"- api_key_secret_id: {identity.get('api_key_secret_id')}",
                "",
            ]
        )
    md_lines.extend(
        [
            "## Notes",
            "- Ticket identifiers are hashed in the JSON report.",
            "- Shopify shop domains are hashed in the JSON report.",
            "- No message bodies or customer identifiers are stored.",
            "- HTTP trace captures urllib.request and AWS SDK (botocore) calls.",
        ]
    )

    return md_lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live read-only shadow evaluation.")
    parser.add_argument(
        "--ticket-id",
        action="append",
        help="Richpanel ticket/conversation id to evaluate (repeatable)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of recent tickets to sample when --ticket-id is not provided",
    )
    parser.add_argument(
        "--max-tickets",
        type=int,
        help="Alias for --sample-size",
    )
    parser.add_argument(
        "--ticket-list-path",
        default="/v1/tickets",
        help="Richpanel API path for ticket listing (default: /v1/tickets)",
    )
    parser.add_argument(
        "--allow-empty-sample",
        action="store_true",
        help="Allow run to complete when ticket listing fails or returns empty",
    )
    parser.add_argument(
        "--allow-ticket-fetch-failures",
        action="store_true",
        help="Continue when a ticket lookup fails; record a warning instead of aborting.",
    )
    parser.add_argument(
        "--allow-non-prod",
        action="store_true",
        help="Allow non-prod runs for local tests",
    )
    parser.add_argument(
        "--env",
        dest="env_name",
        help="Target environment (prod/staging/dev).",
    )
    parser.add_argument(
        "--region",
        help="AWS region for secrets or HTTP trace metadata.",
    )
    parser.add_argument(
        "--stack-name",
        help="Optional stack name (metadata only).",
    )
    parser.add_argument(
        "--run-id",
        help="Optional run id override for artifact filenames",
    )
    parser.add_argument(
        "--out",
        help="Write JSON report to this path (file or directory).",
    )
    parser.add_argument(
        "--summary-md-out",
        help="Optional path for the PII-safe markdown summary.",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Optional override for rp-mw/<env>/richpanel/api_key secret id",
    )
    parser.add_argument(
        "--shop-domain",
        help="Optional Shopify shop domain override (defaults to env)",
    )
    parser.add_argument(
        "--shopify-probe",
        action="store_true",
        help="Probe Shopify with a read-only GET to verify access",
    )
    parser.add_argument(
        "--request-trace",
        action="store_true",
        help="Capture Richpanel request trace to compute burst metrics.",
    )
    parser.add_argument(
        "--skip-conversations",
        action="store_true",
        help=(
            "Skip fetching conversations/messages to reduce Richpanel request volume. "
            "Reduces requests from 3/ticket to 1/ticket."
        ),
    )
    args = parser.parse_args()

    if args.env_name:
        normalized_env = str(args.env_name).strip().lower()
        if normalized_env:
            os.environ["RICHPANEL_ENV"] = normalized_env
            os.environ["MW_ENV"] = normalized_env
            os.environ["ENVIRONMENT"] = normalized_env
            os.environ["RICH_PANEL_ENV"] = normalized_env

    if args.region:
        os.environ["AWS_REGION"] = args.region
        os.environ["AWS_DEFAULT_REGION"] = args.region

    if args.stack_name:
        os.environ["MW_STACK_NAME"] = str(args.stack_name).strip()

    if (
        args.sample_size is not None
        and args.max_tickets is not None
        and args.sample_size != args.max_tickets
    ):
        raise SystemExit("Use --sample-size or --max-tickets (not both)")
    sample_size = (
        args.max_tickets
        if args.max_tickets is not None
        else (args.sample_size if args.sample_size is not None else DEFAULT_SAMPLE_SIZE)
    )

    env_name = _require_prod_environment(allow_non_prod=args.allow_non_prod)
    if not os.environ.get("RICHPANEL_ENV"):
        os.environ["RICHPANEL_ENV"] = env_name

    richpanel_base_url = _resolve_richpanel_base_url()
    is_prod_target = _is_prod_target(
        richpanel_base_url=richpanel_base_url,
        richpanel_secret_id=args.richpanel_secret_id,
    )
    if is_prod_target:
        _require_env_flag(
            "RICHPANEL_WRITE_DISABLED",
            "true",
            context="production Richpanel access",
        )
    enforced_env = _require_env_flags("read-only shadow evaluation")
    if args.shop_domain:
        os.environ["SHOPIFY_SHOP_DOMAIN"] = args.shop_domain

    if args.request_trace:
        os.environ["RICHPANEL_TRACE_ENABLED"] = "true"

    shopify_secrets_client = _resolve_shopify_secrets_client()
    shopify_client = _build_shopify_client(
        allow_network=None,
        shop_domain=args.shop_domain,
        secrets_client=shopify_secrets_client,
    )
    resolved_shop_domain = _normalize_optional_text(
        args.shop_domain or os.environ.get("SHOPIFY_SHOP_DOMAIN")
    )
    resolved_region = _normalize_optional_text(
        args.region
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
    )
    resolved_stack_name = _normalize_optional_text(
        args.stack_name or os.environ.get("MW_STACK_NAME")
    )

    run_id = args.run_id or _build_run_id()
    report_path, summary_path, report_md_path, trace_path = _resolve_output_paths(
        run_id,
        out_path=args.out,
        summary_md_out=args.summary_md_out,
    )

    started_at = datetime.now(timezone.utc)
    run_started = time.monotonic()
    run_warnings: List[str] = []
    ticket_durations: List[float] = []
    ticket_schema_seen: set[str] = set()
    shopify_schema_seen: set[str] = set()
    ticket_schema_total = 0
    ticket_schema_new = 0
    shopify_schema_total = 0
    shopify_schema_new = 0
    ticket_schema_key_counts: Counter[str] = Counter()
    ticket_schema_ignored_counts: Counter[str] = Counter()
    shopify_schema_key_counts: Counter[str] = Counter()
    shopify_schema_ignored_counts: Counter[str] = Counter()

    trace = _HttpTrace().capture()
    had_errors = False
    ticket_results: List[Dict[str, Any]] = []
    ticket_refs: List[str] = []
    sample_mode = "explicit"
    tickets_requested = 0
    shopify_probe: Dict[str, Any] = {"enabled": bool(args.shopify_probe)}
    trace_entries: List[Dict[str, Any]] = []
    trace_enabled = _env_truthy(os.environ.get("RICHPANEL_TRACE_ENABLED"))
    try:
        rp_client = _build_richpanel_client(
            richpanel_secret=args.richpanel_secret_id,
            base_url=richpanel_base_url,
        )
        LOGGER.info("Waiting for rate limit quota to clear...")
        time.sleep(5)

        if args.shopify_probe:
            try:
                probe = _probe_shopify(
                    shop_domain=args.shop_domain,
                    secrets_client=shopify_secrets_client,
                )
                shopify_probe.update(probe)
                if not probe.get("ok", False):
                    shopify_probe["error"] = {"type": "shopify_error"}
                    LOGGER.warning(
                        "Shopify probe failed",
                        extra={
                            "status": probe.get("status_code"),
                            "dry_run": probe.get("dry_run"),
                        },
                    )
            except Exception as exc:
                shopify_probe["error"] = _safe_error(exc)
                LOGGER.warning(
                    "Shopify probe exception",
                    extra={"error_type": shopify_probe["error"]["type"]},
                )

        explicit_refs = [str(value).strip() for value in (args.ticket_id or [])]
        explicit_refs = [value for value in dict.fromkeys(explicit_refs) if value]
        if explicit_refs:
            ticket_refs = explicit_refs
            tickets_requested = len(explicit_refs)
            sample_mode = "explicit"
        else:
            try:
                ticket_refs = _fetch_recent_ticket_refs(
                    rp_client,
                    sample_size=sample_size,
                    list_path=args.ticket_list_path,
                )
            except SystemExit as exc:
                if args.allow_empty_sample:
                    reason = (
                        "ticket_listing_403"
                        if "status 403" in str(exc)
                        else "ticket_listing_failed"
                    )
                    run_warnings.append(reason)
                    LOGGER.warning("Ticket listing failed; continuing with empty sample")
                    ticket_refs = []
                else:
                    raise
            tickets_requested = sample_size
            sample_mode = "recent"

        if not ticket_refs:
            if args.allow_empty_sample and sample_mode == "recent":
                LOGGER.warning("No tickets available for evaluation; continuing")
            else:
                raise SystemExit("No tickets available for evaluation")
        if len(ticket_refs) < tickets_requested:
            LOGGER.warning(
                "Sample size reduced: requested %d got %d",
                tickets_requested,
                len(ticket_refs),
            )

        for ticket_ref in ticket_refs:
            ticket_started = time.monotonic()
            redacted = _redact_identifier(ticket_ref) or "redacted"
            result: Dict[str, Any] = {"ticket_id_redacted": redacted}
            shopify_lookup_ok = True
            if trace_enabled:
                rp_client.clear_request_trace()
            try:
                try:
                    ticket_payload = _fetch_ticket(rp_client, ticket_ref)
                except Exception as exc:
                    if not args.allow_ticket_fetch_failures:
                        raise
                    had_errors = True
                    result["failure_reason"] = "richpanel_ticket_fetch_failed"
                    result["failure_source"] = "richpanel_ticket_fetch"
                    result["error"] = _safe_error(exc)
                    LOGGER.warning(
                        "Ticket fetch failed; continuing",
                        extra={"ticket_id_redacted": redacted},
                    )
                    continue

                ticket_id = str(ticket_payload.get("id") or ticket_ref).strip()
                if args.skip_conversations:
                    convo_payload = {}
                else:
                    convo_payload = _fetch_conversation(
                        rp_client,
                        ticket_id,
                        conversation_id=ticket_payload.get("conversation_id"),
                        conversation_no=ticket_payload.get("conversation_no"),
                    )
                channel_value = _extract_channel(ticket_payload) or _extract_channel(
                    convo_payload
                )
                result["channel"] = _classify_channel(channel_value)

                ticket_schema = _schema_fingerprint(
                    ticket_payload,
                    key_counter=ticket_schema_key_counts,
                    ignored_counter=ticket_schema_ignored_counts,
                )
                if ticket_schema:
                    result["ticket_schema_fingerprint"] = ticket_schema
                    ticket_schema_total += 1
                    if ticket_schema not in ticket_schema_seen:
                        ticket_schema_seen.add(ticket_schema)
                        ticket_schema_new += 1

                order_payload = _extract_order_payload(ticket_payload, convo_payload)
                probe_summary: Dict[str, Any] = {}
                try:
                    probe_summary = lookup_order_summary(
                        build_event_envelope(order_payload),
                        safe_mode=False,
                        automation_enabled=True,
                        allow_network=True,
                        shopify_client=shopify_client,
                    )
                except (ShopifyRequestError, ShopifyTransportError) as exc:
                    shopify_lookup_ok = False
                    had_errors = True
                    result["failure_reason"] = _classify_shopify_exception(exc)
                    result["failure_source"] = "shopify_fetch"
                    result["error"] = _safe_error(exc)

                if isinstance(probe_summary, dict):
                    result["order_resolution"] = probe_summary.get("order_resolution")
                    if shopify_lookup_ok:
                        # Store tracking/shipping data from Shopify lookup (redacted for PII)
                        tracking_num = probe_summary.get("tracking_number")
                        result["shopify_tracking_number"] = bool(tracking_num)
                        result["shopify_tracking_redacted"] = _redact_tracking_number(
                            tracking_num
                        )
                        result["shopify_carrier"] = probe_summary.get("carrier") or None
                        result["shopify_order_created_at"] = bool(
                            probe_summary.get("created_at")
                            or probe_summary.get("order_created_at")
                        )
                        result["shopify_shipping_method"] = (
                            probe_summary.get("shipping_method")
                            or probe_summary.get("shipping_method_name")
                        )
                        # Compute ETA from order date + shipping method + ticket date
                        ticket_created = ticket_payload.get("created_at")
                        eta_result = _compute_eta_for_ticket(
                            probe_summary, ticket_created
                        )
                        if eta_result:
                            result["computed_eta"] = eta_result

                        shopify_schema = _schema_fingerprint(
                            probe_summary,
                            key_counter=shopify_schema_key_counts,
                            ignored_counter=shopify_schema_ignored_counts,
                        )
                        result["shopify_schema_fingerprint"] = shopify_schema
                        shopify_schema_total += 1
                        if shopify_schema not in shopify_schema_seen:
                            shopify_schema_seen.add(shopify_schema)
                            shopify_schema_new += 1

                raw_customer_message = _extract_latest_customer_message(
                    ticket_payload, convo_payload
                )
                customer_message = raw_customer_message or "(not provided)"
                comment_metadata = summarize_comment_metadata(ticket_payload)
                result.update(comment_metadata)
                result["customer_message_present"] = bool(raw_customer_message)
                event_payload = dict(order_payload)
                event_payload.update(
                    {
                        "ticket_id": ticket_ref,
                        "conversation_id": ticket_payload.get("conversation_id")
                        or ticket_id,
                        "customer_message": customer_message,
                    }
                )

                envelope = normalize_event({"payload": event_payload})
                plan = plan_actions(
                    envelope,
                    safe_mode=False,
                    automation_enabled=True,
                    allow_network=True,
                    outbound_enabled=False,
                )

                result["routing"] = _build_route_info(
                    getattr(plan, "routing", None),
                    getattr(plan, "routing_artifact", None),
                )
                result["would_reply_send"] = any(
                    isinstance(action, dict)
                    and action.get("type") in SEND_ACTION_TYPES
                    for action in plan.actions
                )

                order_action = next(
                    (
                        a
                        for a in plan.actions
                        if isinstance(a, dict)
                        and a.get("type") == "order_status_draft_reply"
                    ),
                    None,
                )
                parameters = (
                    order_action.get("parameters", {})
                    if isinstance(order_action, dict)
                    else {}
                )
                order_summary = (
                    parameters.get("order_summary")
                    if isinstance(parameters, dict)
                    else {}
                )
                # Merge probe_summary into order_summary if we have it
                # Use isinstance check for consistency with other defensive checks
                effective_summary = (
                    dict(probe_summary) if isinstance(probe_summary, dict) else {}
                )
                if order_summary:
                    effective_summary.update(order_summary)

                result.update(
                    _order_context_summary(
                        order_payload,
                        effective_summary,
                        conversation_id=str(
                            ticket_payload.get("conversation_id") or ticket_id
                        ),
                    )
                )
                delivery_estimate = (
                    parameters.get("delivery_estimate")
                    if isinstance(parameters, dict)
                    else None
                )

                # Use probe_summary (Shopify data) for tracking detection
                tracking_found = _tracking_present(effective_summary)
                # ETA is available if we have delivery_estimate OR order_created_at
                has_order_date = bool(
                    effective_summary.get("created_at")
                    or effective_summary.get("order_created_at")
                    or order_payload.get("created_at")
                    or order_payload.get("order_created_at")
                )
                # Check both shipping_method and shipping_method_name for consistency
                # with _compute_eta_for_ticket which uses either field
                has_shipping_method = bool(
                    effective_summary.get("shipping_method")
                    or effective_summary.get("shipping_method_name")
                )
                eta_available = _delivery_estimate_present(delivery_estimate) or (
                    has_order_date and has_shipping_method
                )

                # order_matched should be true if we resolved an order (not just draft reply)
                # Safely handle order_resolution being None (not just absent)
                order_resolution = (
                    probe_summary.get("order_resolution")
                    if isinstance(probe_summary, dict)
                    else None
                )
                order_resolved = (
                    isinstance(order_resolution, dict)
                    and order_resolution.get("resolvedBy") not in (None, "no_match")
                    and _extract_shopify_diagnostics_category(order_resolution)
                    not in {"auth_fail", "rate_limited", "http_error"}
                )

                result.update(
                    {
                        "order_status_candidate": bool(order_action),
                        "order_matched": bool(order_summary) or order_resolved,
                        "tracking_found": tracking_found,
                        "eta_available": eta_available,
                    }
                )
                if "failure_reason" not in result:
                    match_failure = _classify_order_match_failure(result)
                    if match_failure:
                        result["failure_reason"] = match_failure
                        result["failure_source"] = "order_match"
            except SystemExit as exc:
                if args.allow_ticket_fetch_failures and "Ticket lookup failed" in str(
                    exc
                ):
                    result["failure_reason"] = "ticket_fetch_failed"
                    result["failure_source"] = "richpanel_fetch"
                    result["error"] = {"type": "richpanel_error"}
                    run_warnings.append("ticket_fetch_failed")
                else:
                    raise
            except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
                had_errors = True
                result["failure_reason"] = _classify_richpanel_exception(exc)
                result["failure_source"] = "richpanel_fetch"
                result["error"] = _safe_error(exc)
            except Exception as exc:
                had_errors = True
                result["failure_reason"] = "unexpected_error"
                result["failure_source"] = "unknown"
                result["error"] = _safe_error(exc)
            finally:
                elapsed = time.monotonic() - ticket_started
                result["elapsed_seconds"] = round(elapsed, 3)
                ticket_durations.append(elapsed)
                ticket_results.append(result)
                if trace_enabled:
                    ticket_trace = rp_client.get_request_trace()
                    trace_entries.extend(ticket_trace)
                    result["richpanel_request_count"] = len(ticket_trace)
                    endpoint_counts: Counter[str] = Counter()
                    for entry in ticket_trace:
                        path = entry.get("path")
                        if path:
                            endpoint_counts[path] += 1
                    result["richpanel_request_counts_by_endpoint"] = dict(
                        endpoint_counts
                    )

    finally:
        trace.stop()
        with trace_path.open("w", encoding="utf-8") as fh:
            json.dump(trace.to_dict(), fh, ensure_ascii=False, indent=2)
        openai_allow_network = _to_bool(os.environ.get("OPENAI_ALLOW_NETWORK"), False)
        allow_openai = (
            openai_allow_network
            and _openai_any_enabled()
            and (
                _to_bool(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"), False)
                or _openai_shadow_enabled()
            )
        )
        trace.assert_read_only(allow_openai=allow_openai, trace_path=trace_path)

    trace_summary = _summarize_trace(trace, allow_openai=allow_openai)
    counts = {
        "tickets_requested": tickets_requested,
        "tickets_selected": len(ticket_refs),
        "tickets_scanned": len(ticket_results),
        "order_status_candidates": sum(
            1 for item in ticket_results if item.get("order_status_candidate")
        ),
        "orders_matched": sum(1 for item in ticket_results if item.get("order_matched")),
        "tracking_found": sum(1 for item in ticket_results if item.get("tracking_found")),
        "eta_available": sum(1 for item in ticket_results if item.get("eta_available")),
        "tracking_or_eta_available": sum(
            1
            for item in ticket_results
            if item.get("tracking_found") or item.get("eta_available")
        ),
        "errors": sum(1 for item in ticket_results if item.get("error")),
    }
    request_burst = _summarize_request_burst(trace_entries)
    retry_after_validation = _summarize_retry_after(trace_entries)

    schema_key_stats: Optional[Dict[str, Any]] = None
    if (
        ticket_schema_key_counts
        or ticket_schema_ignored_counts
        or shopify_schema_key_counts
        or shopify_schema_ignored_counts
    ):
        schema_key_stats = _build_schema_key_stats(
            ticket_keys=ticket_schema_key_counts,
            ticket_ignored=ticket_schema_ignored_counts,
            shopify_keys=shopify_schema_key_counts,
            shopify_ignored=shopify_schema_ignored_counts,
        )

    drift_summary = _build_drift_summary(
        ticket_total=ticket_schema_total,
        ticket_new=ticket_schema_new,
        ticket_unique=len(ticket_schema_seen),
        shopify_total=shopify_schema_total,
        shopify_new=shopify_schema_new,
        shopify_unique=len(shopify_schema_seen),
        threshold=DRIFT_WARNING_THRESHOLD,
    )
    
    # B61/C: Build drift watch with current metrics
    drift_watch = _compute_drift_watch(
        ticket_results=ticket_results,
        ticket_schema_total=ticket_schema_total,
        ticket_schema_new=ticket_schema_new,
        shopify_schema_total=shopify_schema_total,
        shopify_schema_new=shopify_schema_new,
    )
    
    timing_summary = _summarize_timing(
        ticket_durations, run_duration_seconds=time.monotonic() - run_started
    )
    summary_payload = _build_summary_payload(
        run_id=run_id,
        tickets_requested=tickets_requested,
        ticket_results=ticket_results,
        timing=timing_summary,
        drift=drift_summary,
        schema_key_stats=schema_key_stats,
        run_warnings=run_warnings,
    )
    # Add drift watch to summary
    summary_payload["drift_watch"] = drift_watch

    report = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": env_name,
        "env_flags": enforced_env,
        "target": {
            "env": env_name,
            "region": resolved_region or None,
            "stack_name": resolved_stack_name or None,
            "richpanel_base_url": richpanel_base_url,
            "shop_domain": _redact_shop_domain(resolved_shop_domain),
        },
        "prod_target": is_prod_target,
        "sample_mode": sample_mode,
        "conversation_mode": "skipped" if args.skip_conversations else "full",
        "ticket_count": summary_payload.get("ticket_count", counts["tickets_scanned"]),
        "match_success_rate": summary_payload.get("match_success_rate", 0.0),
        "match_failure_buckets": summary_payload.get("match_failure_buckets", {}),
        "tracking_or_eta_available_rate": summary_payload.get(
            "tracking_or_eta_available_rate", 0.0
        ),
        "would_reply_send": summary_payload.get("would_reply_send", False),
        "top_failure_reasons": summary_payload.get("top_failure_reasons", []),
        "counts": counts,
        "shopify_probe": shopify_probe,
        "tickets": ticket_results,
        "summary_path": str(summary_path),
        "run_warnings": list(run_warnings),
        "http_trace_path": str(trace_path),
        "http_trace_summary": trace_summary,
        "richpanel_request_burst": request_burst or None,
        "richpanel_retry_after_validation": retry_after_validation or None,
        "richpanel_identity": _build_identity_block(
            client=rp_client,
            env_name=env_name,
            started_at=started_at,
            duration_seconds=time.monotonic() - run_started,
        ),
        "notes": [
            "Ticket identifiers are hashed.",
            "Shopify shop domains are hashed.",
            "No message bodies or customer identifiers are stored.",
            "HTTP trace captures urllib.request and AWS SDK (botocore) calls; "
            "entries include source and AWS operation metadata.",
        ],
    }

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_lines = _build_markdown_report(report, summary_payload)
    report_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    LOGGER.info(
        "Shadow eval summary: run_id=%s tickets_scanned=%d orders_matched=%d "
        "tracking_found=%d eta_available=%d errors=%d",
        run_id,
        counts["tickets_scanned"],
        counts["orders_matched"],
        counts["tracking_found"],
        counts["eta_available"],
        counts["errors"],
    )
    LOGGER.info("Report written to %s", report_path)
    LOGGER.info("Summary written to %s", summary_path)
    LOGGER.info("HTTP trace written to %s", trace_path)
    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
