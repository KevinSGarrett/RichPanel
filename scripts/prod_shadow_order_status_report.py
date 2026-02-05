#!/usr/bin/env python3
"""
Live read-only shadow report for Order Status readiness (prod data, no writes).

- Reads Richpanel tickets + Shopify orders in read-only mode
- Uses deterministic order-status routing (no OpenAI calls)
- Emits PII-safe JSON + Markdown report artifacts
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from richpanel_middleware.automation.delivery_estimate import (  # type: ignore
    compute_delivery_estimate,
)
from richpanel_middleware.automation.llm_routing import (  # type: ignore
    compute_dual_routing,
)
from richpanel_middleware.automation.order_status_intent import (  # type: ignore
    classify_order_status_intent,
    redact_ticket_text,
)
from richpanel_middleware.automation.router import (  # type: ignore
    extract_customer_message,
)
from richpanel_middleware.commerce import order_lookup  # type: ignore
from richpanel_middleware.commerce.order_lookup import (  # type: ignore
    lookup_order_summary,
)
from richpanel_middleware.ingest.envelope import build_event_envelope  # type: ignore
from richpanel_middleware.integrations.richpanel import (  # type: ignore
    RichpanelRequestError,
    SecretLoadError,
    TransportError as RichpanelTransportError,
)
from richpanel_middleware.integrations.shopify import (  # type: ignore
    ShopifyRequestError,
    TransportError as ShopifyTransportError,
)
from richpanel_middleware.integrations.shipstation import (  # type: ignore
    ShipStationClient,
)
from readonly_shadow_utils import (
    GuardedRichpanelClient,
    GuardedShopifyClient,
    ReadOnlyHttpGuard,
    ReadOnlyGuardError,
    _redact_path,
    extract_comment_message,
    extract_order_number,
    extract_ticket_fields,
    fetch_recent_ticket_refs,
    safe_error,
)
from aws_account_preflight import ENV_ACCOUNT_IDS, normalize_env
from secrets_preflight import run_secrets_preflight

LOGGER = logging.getLogger("prod_shadow_order_status")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("richpanel_middleware").setLevel(logging.WARNING)
logging.getLogger("integrations").setLevel(logging.WARNING)

ORDER_STATUS_INTENTS = {
    "order_status_tracking",
    "shipping_delay_not_shipped",
    "order_status_delivery_issue",
}
DEFAULT_SAMPLE_SIZE = 25
PROD_ENV_NAMES = {"prod", "production"}

REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_READ_ONLY": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
    "RICHPANEL_OUTBOUND_ENABLED": "false",
    "MW_OPENAI_ROUTING_ENABLED": "true",
    "MW_OPENAI_INTENT_ENABLED": "true",
    "MW_OPENAI_SHADOW_ENABLED": "true",
}
SHOPIFY_REQUIRED_FLAGS = {
    "SHOPIFY_OUTBOUND_ENABLED": "true",
    "SHOPIFY_WRITE_DISABLED": "true",
}


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
    client: GuardedRichpanelClient,
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


class _RichpanelRetryDiagnostics(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.total_retries = 0
        self.status_counts: Counter[int] = Counter()
        self.status_family_counts: Counter[str] = Counter()
        self.endpoint_counts: Counter[str] = Counter()
        self.endpoint_status_counts: Dict[str, Counter[int]] = defaultdict(Counter)
        self.attempt_counts: Counter[int] = Counter()
        self.retry_delay_samples: list[float] = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.msg != "richpanel.retry":
            return
        self.total_retries += 1
        status = getattr(record, "status", None)
        if isinstance(status, int):
            self.status_counts[status] += 1
            if status == 429:
                self.status_family_counts["429"] += 1
            elif 500 <= status < 600:
                self.status_family_counts["5xx"] += 1
            else:
                self.status_family_counts["other"] += 1
        attempt = getattr(record, "attempt", None)
        if attempt is not None:
            try:
                self.attempt_counts[int(attempt)] += 1
            except (TypeError, ValueError):
                pass
        retry_in = getattr(record, "retry_in", None)
        if retry_in is not None:
            try:
                self.retry_delay_samples.append(float(retry_in))
            except (TypeError, ValueError):
                pass
        url = getattr(record, "url", None)
        path_redacted = _redact_url_path(url)
        self.endpoint_counts[path_redacted] += 1
        if isinstance(status, int):
            self.endpoint_status_counts[path_redacted][status] += 1


def _redact_url_path(url: Optional[str]) -> str:
    if not url:
        return "/"
    try:
        path = urllib.parse.urlparse(url).path
    except Exception:
        path = url
    return _redact_path(path)


def _summarize_retry_diagnostics(handler: _RichpanelRetryDiagnostics) -> Dict[str, Any]:
    if handler.total_retries == 0:
        return {}
    delay_stats: Dict[str, float] = {}
    if handler.retry_delay_samples:
        delay_stats = {
            "min_seconds": round(min(handler.retry_delay_samples), 3),
            "max_seconds": round(max(handler.retry_delay_samples), 3),
            "avg_seconds": round(
                sum(handler.retry_delay_samples) / len(handler.retry_delay_samples), 3
            ),
        }
    endpoints: list[Dict[str, Any]] = []
    for path, count in handler.endpoint_counts.most_common(10):
        status_counts = handler.endpoint_status_counts.get(path) or Counter()
        endpoints.append(
            {
                "path_redacted": path,
                "retry_count": count,
                "status_counts": dict(status_counts),
            }
        )
    return {
        "total_retries": handler.total_retries,
        "status_counts": dict(handler.status_counts),
        "status_family_counts": dict(handler.status_family_counts),
        "attempt_counts": dict(handler.attempt_counts),
        "retry_delay_seconds": delay_stats,
        "top_retry_endpoints": endpoints,
    }


def _build_retry_proof(
    *,
    run_id: str,
    env_name: str,
    retry_diagnostics: Dict[str, Any],
    trace_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": env_name,
        "richpanel_http_max_attempts": os.environ.get("RICHPANEL_HTTP_MAX_ATTEMPTS"),
        "retry_diagnostics": retry_diagnostics or {},
        "retry_after_validation": _summarize_retry_after(trace_entries),
        "request_burst": _summarize_request_burst(trace_entries),
        "trace_entry_count": len(trace_entries),
    }


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


def _resolve_env_name() -> str:
    raw = (
        os.environ.get("RICHPANEL_ENV")
        or os.environ.get("RICH_PANEL_ENV")
        or os.environ.get("MW_ENV")
        or os.environ.get("ENVIRONMENT")
        or "local"
    )
    return str(raw).strip().lower() or "local"


def _require_env_flag(key: str, expected: str, *, context: str) -> None:
    actual = os.environ.get(key)
    if actual is None:
        raise SystemExit(f"{key} must be {expected} for {context} (unset)")
    if str(actual).strip().lower() != expected:
        raise SystemExit(f"{key} must be {expected} for {context} (found {actual})")


def _require_env_flags(context: str) -> Dict[str, str]:
    applied: Dict[str, str] = {}
    for key, expected in REQUIRED_FLAGS.items():
        _require_env_flag(key, expected, context=context)
        applied[key] = expected
    for key, expected in SHOPIFY_REQUIRED_FLAGS.items():
        _require_env_flag(key, expected, context=context)
        applied[key] = expected
    return applied


def _require_prod_environment(*, allow_non_prod: bool) -> str:
    env_name = _resolve_env_name()
    if env_name in PROD_ENV_NAMES:
        return env_name
    if allow_non_prod:
        return env_name
    raise SystemExit(
        "ENVIRONMENT must resolve to prod for this report "
        "(use --allow-non-prod for local tests)"
    )


def _redact_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = str(value)
    parts = text.split("T")[0].split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}-XX"
    return None


def _extract_channel(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    via = payload.get("via")
    channel = None
    if isinstance(via, dict):
        channel = via.get("channel")
    if channel is None:
        channel = payload.get("channel")
    return str(channel or "").strip().lower()


def _classify_channel(channel: str) -> str:
    if not channel:
        return "unknown"
    if channel == "email":
        return "email"
    if "chat" in channel:
        return "chat"
    return "unknown"


def _fetch_ticket(client: GuardedRichpanelClient, ticket_ref: str) -> Dict[str, Any]:
    ticket_text = str(ticket_ref).strip()
    encoded = urllib.parse.quote(ticket_text, safe="")
    if ticket_text.isdigit():
        # Numeric refs are ticket numbers; avoid extra calls to reduce rate limits.
        attempts = (f"/v1/tickets/number/{encoded}",)
    else:
        attempts = (f"/v1/tickets/{encoded}", f"/v1/tickets/number/{encoded}")
    errors: list[str] = []
    for path in attempts:
        try:
            resp = client.request("GET", path, dry_run=False, log_body_excerpt=False)
        except (RichpanelRequestError, SecretLoadError, RichpanelTransportError) as exc:
            errors.append(f"{path}: {exc.__class__.__name__}")
            continue
        if resp.dry_run or resp.status_code >= 400:
            errors.append(f"{path}: status {resp.status_code} dry_run={resp.dry_run}")
            continue
        payload = resp.json() or {}
        if isinstance(payload, dict) and isinstance(payload.get("ticket"), dict):
            payload = payload["ticket"]
        return payload if isinstance(payload, dict) else {}
    redacted_ref = _redact_identifier(ticket_ref) or "redacted"
    raise SystemExit(f"Ticket lookup failed for {redacted_ref}: {'; '.join(errors)}")


def _fetch_conversation(
    client: GuardedRichpanelClient,
    ticket_id: str,
    *,
    conversation_id: Optional[str] = None,
    conversation_no: Optional[object] = None,
) -> Dict[str, Any]:
    candidate = ""
    for value in (conversation_id, conversation_no, ticket_id):
        if value is None:
            continue
        text = str(value).strip()
        if text:
            candidate = text
            break

    if not candidate:
        return {}

    attempts = (
        "/v1/conversations/{encoded}",
        "/v1/conversations/{encoded}/messages",
    )
    encoded = urllib.parse.quote(candidate, safe="")
    for template in attempts:
        path = template.format(encoded=encoded)
        try:
            resp = client.request("GET", path, dry_run=False, log_body_excerpt=False)
        except Exception:
            continue
        if resp.dry_run or resp.status_code >= 400:
            continue
        payload = resp.json()
        if isinstance(payload, list):
            payload = {"messages": payload}
        if isinstance(payload, dict) and isinstance(payload.get("conversation"), dict):
            convo = dict(payload.get("conversation") or {})
            if isinstance(payload.get("messages"), list) and "messages" not in convo:
                convo["messages"] = payload["messages"]
            payload = convo
        return payload if isinstance(payload, dict) else {}
    return {}


def _extract_latest_customer_message(ticket: Dict[str, Any], convo: Dict[str, Any]) -> str:
    text = extract_customer_message(ticket, default="")
    if text:
        return text
    text = extract_comment_message(ticket, extractor=extract_customer_message)
    if text:
        return text
    text = extract_customer_message(convo, default="")
    if text:
        return text
    text = extract_comment_message(convo, extractor=extract_customer_message)
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


def _build_order_payload(ticket: Dict[str, Any], convo: Dict[str, Any]) -> Dict[str, Any]:
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


def _compute_eta_window(
    order_summary: Dict[str, Any], ticket_created_at: Optional[str]
) -> Optional[str]:
    order_created = (
        order_summary.get("created_at") or order_summary.get("order_created_at")
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
    eta_human = estimate.get("eta_human")
    if eta_human:
        return str(eta_human)
    window_min = estimate.get("window_min_days")
    window_max = estimate.get("window_max_days")
    if window_min is None or window_max is None:
        return None
    return f"{window_min}-{window_max} business days"


def _match_result(
    *,
    order_summary: Dict[str, Any],
    order_number_present: bool,
    email_present: bool,
    shopify_calls: int,
    error: Optional[Dict[str, str]],
) -> str:
    if error:
        return "error"
    resolution = order_summary.get("order_resolution")
    resolved_by = ""
    diagnostics_category = None
    if isinstance(resolution, dict):
        resolved_by = str(resolution.get("resolvedBy") or "")
        diagnostics = resolution.get("shopify_diagnostics")
        if isinstance(diagnostics, dict):
            diagnostics_category = str(diagnostics.get("category") or "").strip().lower()
    if diagnostics_category in {"auth_fail", "rate_limited", "http_error"}:
        return "error"
    if resolved_by:
        resolved_by_lower = resolved_by.lower()
        if "order_number" in resolved_by_lower:
            return "matched_by_order_number"
        if "email" in resolved_by_lower:
            return "matched_by_email"
        if resolved_by_lower == "no_match":
            return "no_match"
    if shopify_calls > 0:
        if order_number_present:
            return "matched_by_order_number"
        if email_present:
            return "matched_by_email"
    return "no_match"


def _failure_mode(
    *,
    match_result: str,
    order_number_present: bool,
    email_present: bool,
    error: Optional[Dict[str, str]],
    order_resolution: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    if match_result == "error":
        if error:
            return error.get("type") or "error"
        if isinstance(order_resolution, dict):
            diagnostics = order_resolution.get("shopify_diagnostics")
            if isinstance(diagnostics, dict):
                category = str(diagnostics.get("category") or "").strip().lower()
                if category in {"auth_fail", "rate_limited", "http_error"}:
                    return f"shopify_{category}"
        return "error"
    if match_result != "no_match":
        return None
    if not order_number_present and not email_present:
        return "missing_order_number_and_email"
    if not order_number_present:
        return "missing_order_number"
    if not email_present:
        return "missing_email"
    return "no_shopify_match"


class _InstrumentedShopifyClient(GuardedShopifyClient):
    def __init__(self, *args: Any, guard: ReadOnlyHttpGuard, **kwargs: Any) -> None:
        super().__init__(*args, guard=guard, **kwargs)
        self.request_count = 0

    def request(self, method: str, path: str, *args: Any, **kwargs: Any):  # type: ignore[override]
        self.request_count += 1
        return super().request(method, path, *args, **kwargs)


def _build_run_id() -> str:
    return datetime.now(timezone.utc).strftime("RUN_%Y%m%d_%H%MZ")


def _build_markdown_report(report: Dict[str, Any]) -> str:
    stats = report.get("stats", {})
    stats_global = report.get("stats_global", {}) or {}
    stats_order_status = report.get("stats_order_status", {}) or {}
    failure_modes = report.get("failure_modes", [])
    order_status_failure_modes = report.get("order_status_failure_modes", [])
    run_id = report.get("run_id", "RUN_UNKNOWN")
    timestamp = report.get("timestamp", "")
    env_name = report.get("environment", "unknown")
    classifier = report.get("classification_source", "deterministic")
    env_flags = report.get("env_flags", {}) or {}
    classification_counts = report.get("classification_source_counts", {})
    order_status_rate = report.get("order_status_rate")
    ticket_count = report.get("ticket_count", 0)
    conversation_mode = report.get("conversation_mode", "full")
    retry_diag = report.get("richpanel_retry_diagnostics") or {}
    request_burst = report.get("richpanel_request_burst") or {}
    retry_after_validation = report.get("richpanel_retry_after_validation") or {}
    identity = report.get("richpanel_identity") or {}

    classification_summary = ", ".join(
        f"{key}: {value}" for key, value in classification_counts.items()
    )
    order_status_rate_pct = (
        f"{order_status_rate * 100:.1f}%" if isinstance(order_status_rate, float) else "n/a"
    )
    order_status_count = stats_order_status.get(
        "order_status_count", stats.get("classified_order_status_true", 0)
    )
    match_rate_pct = (
        f"{stats_order_status.get('match_rate_among_order_status', 0) * 100:.1f}%"
        if isinstance(stats_order_status.get("match_rate_among_order_status"), float)
        else "n/a"
    )
    tracking_rate_pct = (
        f"{stats_order_status.get('tracking_rate', 0) * 100:.1f}%"
        if isinstance(stats_order_status.get("tracking_rate"), float)
        else "n/a"
    )
    eta_rate_pct = (
        f"{stats_order_status.get('eta_rate_when_no_tracking', 0) * 100:.1f}%"
        if isinstance(stats_order_status.get("eta_rate_when_no_tracking"), float)
        else "n/a"
    )
    env_flag_lines = [f"- `{key}={value}`" for key, value in sorted(env_flags.items())]
    summary_lines = [
        "# Prod Shadow Order Status Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Generated (UTC): {timestamp}",
        f"- Environment: `{env_name}`",
        f"- Classification source: `{classifier}`",
        f"- Classification source counts: {classification_summary or 'n/a'}",
        f"- Tickets scanned: {ticket_count}",
        f"- Conversation mode: `{conversation_mode}`",
        "",
        "## How to Read This Report",
        "- Global stats use all tickets scanned as the denominator.",
        "- Order-status subset stats use only tickets classified as order-status.",
        "",
        "## Env flags",
        *env_flag_lines,
        "",
        "## Executive Summary",
        (
            f"- Order-status subset: {order_status_count} tickets; "
            f"{stats_order_status.get('matched_by_order_number', 0)} matched by "
            f"order number and {stats_order_status.get('matched_by_email', 0)} matched by email."
        ),
        f"- Global order-status rate: {order_status_rate_pct}",
        f"- Match rate among order-status: {match_rate_pct}",
        (
            f"- Tracking present for {stats_order_status.get('tracking_present_count', 0)} "
            f"order-status tickets; ETA available for "
            f"{stats_order_status.get('eta_available_count', 0)} when no tracking."
        ),
        (
            f"- OpenAI routing calls: {stats.get('openai_routing_called', 0)}; "
            f"OpenAI intent calls: {stats.get('openai_intent_called', 0)}."
        ),
        f"- Errors: {stats.get('errors', 0)}",
        "",
        "## Stats (Global: all tickets scanned)",
        "| Metric | Count |",
        "| --- | --- |",
        f"| Tickets scanned | {stats_global.get('tickets_scanned', 0)} |",
        f"| Classified order status (true) | {stats_global.get('classified_order_status_true', 0)} |",
        f"| Classified order status (false) | {stats_global.get('classified_order_status_false', 0)} |",
        f"| Order-status rate | {order_status_rate_pct} |",
        f"| OpenAI routing called | {stats_global.get('openai_routing_called', 0)} |",
        f"| OpenAI intent called | {stats_global.get('openai_intent_called', 0)} |",
        f"| Shopify lookup forced | {stats_global.get('shopify_lookup_forced', 0)} |",
        f"| Richpanel retries (total) | {stats_global.get('richpanel_retry_total', 0)} |",
        f"| Richpanel 429 retries | {stats_global.get('richpanel_retry_429_count', 0)} |",
        f"| Errors | {stats_global.get('errors', 0)} |",
        "",
        "## Stats (Order-status subset only)",
        "| Metric | Count |",
        "| --- | --- |",
        f"| Order-status count | {stats_order_status.get('order_status_count', 0)} |",
        f"| Match attempted | {stats_order_status.get('match_attempted_count', 0)} |",
        f"| Matched by order number | {stats_order_status.get('matched_by_order_number', 0)} |",
        f"| Matched by email | {stats_order_status.get('matched_by_email', 0)} |",
        f"| Match rate among order-status | {match_rate_pct} |",
        f"| Tracking present | {stats_order_status.get('tracking_present_count', 0)} |",
        f"| Tracking rate | {tracking_rate_pct} |",
        f"| ETA available when no tracking | {stats_order_status.get('eta_available_count', 0)} |",
        f"| ETA rate when no tracking | {eta_rate_pct} |",
        "",
        "## Top Failure Modes (Order-status subset)",
    ]

    if order_status_failure_modes:
        for entry in order_status_failure_modes:
            summary_lines.append(f"- {entry['mode']}: {entry['count']}")
    else:
        summary_lines.append("- None observed in this sample.")

    suggestions = []
    if stats.get("missing_order_number", 0):
        suggestions.append("Ensure order number is captured in inbound messages.")
    if stats.get("missing_email", 0):
        suggestions.append("Ensure customer email is available on tickets.")
    if stats.get("shopify_error", 0):
        suggestions.append("Re-validate Shopify read-only token/scopes.")
    if not suggestions:
        suggestions.append("No immediate blockers detected in this sample.")

    summary_lines.extend(
        [
            "",
            "## What to Fix Next",
            *[f"- {item}" for item in suggestions],
            "",
            "## Notes",
            "- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.",
            "- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).",
            "- No outbound messages are sent; would_auto_reply is theoretical only.",
        ]
    )
    if retry_diag:
        status_counts = retry_diag.get("status_counts", {})
        status_summary = ", ".join(
            f"{key}: {value}" for key, value in status_counts.items()
        )
        top_endpoints = retry_diag.get("top_retry_endpoints", [])
        top_lines = []
        for entry in top_endpoints:
            top_lines.append(
                f"- {entry.get('path_redacted')}: {entry.get('retry_count')}"
            )
        summary_lines.extend(
            [
                "",
                "## Richpanel Retry Diagnostics",
                f"- Total retries: {retry_diag.get('total_retries', 0)}",
                f"- Status counts: {status_summary or 'none'}",
                *top_lines,
            ]
        )
    if request_burst:
        summary_lines.extend(
            [
                "",
                "## Richpanel Burst Summary (30s)",
                (
                    f"- Max requests in any 30s window: "
                    f"{request_burst.get('max_requests_overall', 0)}"
                ),
            ]
        )
    if retry_after_validation:
        summary_lines.extend(
            [
                "",
                "## Retry-After Validation",
                (
                    f"- Checked: {retry_after_validation.get('checked', 0)}; "
                    f"violations: {retry_after_validation.get('violations', 0)}"
                ),
            ]
        )
    if identity:
        summary_lines.extend(
            [
                "",
                "## Richpanel Identity",
                f"- base_url: {identity.get('richpanel_base_url')}",
                f"- resolved_env: {identity.get('resolved_env')}",
                f"- api_key_hash: {identity.get('api_key_hash')}",
                f"- api_key_secret_id: {identity.get('api_key_secret_id')}",
            ]
        )
    return "\n".join(summary_lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prod read-only shadow report for order status."
    )
    parser.add_argument(
        "--ticket-number",
        action="append",
        help="Richpanel ticket number or conversation number (repeatable).",
    )
    parser.add_argument(
        "--ticket-id",
        action="append",
        help="Richpanel ticket or conversation id (repeatable).",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of recent tickets to sample when explicit tickets are not provided.",
    )
    parser.add_argument("--max-tickets", type=int, help="Alias for --sample-size.")
    parser.add_argument(
        "--ticket-list-path",
        default="/v1/tickets",
        help="Richpanel API path for ticket listing (default: /v1/tickets).",
    )
    parser.add_argument(
        "--allow-empty-sample",
        action="store_true",
        help="Allow run to complete when ticket listing fails or returns empty.",
    )
    parser.add_argument(
        "--allow-ticket-fetch-failures",
        action="store_true",
        help="Continue when a ticket lookup fails; record an error instead of aborting.",
    )
    parser.add_argument(
        "--retry-diagnostics",
        action="store_true",
        help="Collect Richpanel retry diagnostics (status codes, retry delays, endpoints).",
    )
    parser.add_argument(
        "--force-shopify-lookup",
        action="store_true",
        help=(
            "Force Shopify lookup even when the deterministic router does not classify "
            "order status (shadow-only; still read-only)."
        ),
    )
    parser.add_argument(
        "--request-trace",
        action="store_true",
        help="Capture Richpanel request trace to compute burst metrics.",
    )
    parser.add_argument(
        "--skip-conversations",
        action="store_true",
        help="Skip conversation fetches to reduce Richpanel request volume.",
    )
    parser.add_argument(
        "--skip-openai-intent",
        action="store_true",
        help="Skip OpenAI intent calls (deterministic-only baseline).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Process tickets in smaller batches (0 = no batching).",
    )
    parser.add_argument(
        "--throttle-seconds",
        type=float,
        default=0.0,
        help="Sleep this many seconds between ticket fetches (0 = no throttle).",
    )
    parser.add_argument(
        "--batch-delay-seconds",
        type=float,
        default=0.0,
        help="Sleep this many seconds between batches (0 = no batch delay).",
    )
    parser.add_argument(
        "--allow-non-prod",
        action="store_true",
        help="Allow non-prod runs for local tests.",
    )
    parser.add_argument(
        "--region",
        help="AWS region override for account/secrets preflight (default: env/AWS default).",
    )
    parser.add_argument(
        "--aws-profile",
        help="AWS profile name for Secrets Manager preflight.",
    )
    parser.add_argument(
        "--expect-account-id",
        help="Expected AWS account id for Secrets Manager preflight.",
    )
    parser.add_argument(
        "--require-secret",
        action="append",
        default=[],
        help="Require a Secrets Manager secret id (repeatable).",
    )
    parser.add_argument(
        "--preflight-secrets",
        dest="preflight_secrets",
        action="store_true",
        help="Run AWS account + secrets preflight (default).",
    )
    parser.add_argument(
        "--no-preflight-secrets",
        dest="preflight_secrets",
        action="store_false",
        help="Skip AWS account + secrets preflight.",
    )
    parser.set_defaults(preflight_secrets=True)
    parser.add_argument("--env", dest="env_name", help="Target environment name.")
    parser.add_argument("--richpanel-secret-id", help="Richpanel secret id override.")
    parser.add_argument("--shopify-secret-id", help="Shopify secret id override.")
    parser.add_argument("--shop-domain", help="Shopify shop domain override.")
    parser.add_argument("--run-id", help="Optional run id override.")
    parser.add_argument("--out-json", required=True, help="Output JSON report path.")
    parser.add_argument("--out-md", required=True, help="Output markdown report path.")
    parser.add_argument(
        "--retry-proof-path",
        help="Optional path to write Richpanel retry proof JSON.",
    )
    args = parser.parse_args()

    if args.env_name:
        normalized_env = str(args.env_name).strip().lower()
        if normalized_env:
            os.environ["RICHPANEL_ENV"] = normalized_env
            os.environ["MW_ENV"] = normalized_env
            os.environ["ENVIRONMENT"] = normalized_env
            os.environ["RICH_PANEL_ENV"] = normalized_env

    if args.sample_size is not None and args.max_tickets is not None:
        if args.sample_size != args.max_tickets:
            raise SystemExit("Use --sample-size or --max-tickets (not both)")
    sample_size = (
        args.max_tickets
        if args.max_tickets is not None
        else (args.sample_size if args.sample_size is not None else DEFAULT_SAMPLE_SIZE)
    )
    if sample_size < 1:
        raise SystemExit("--sample-size/--max-tickets must be >= 1")
    if args.batch_size is not None and args.batch_size < 0:
        raise SystemExit("--batch-size must be >= 0")
    if args.throttle_seconds < 0:
        raise SystemExit("--throttle-seconds must be >= 0")
    if args.batch_delay_seconds < 0:
        raise SystemExit("--batch-delay-seconds must be >= 0")

    env_name = _require_prod_environment(allow_non_prod=args.allow_non_prod)
    if args.preflight_secrets:
        LOGGER.info("Running AWS account + secrets preflight...")
        preflight_env = normalize_env(env_name)
        expected_account_id = args.expect_account_id or ENV_ACCOUNT_IDS.get(preflight_env)
        if not expected_account_id:
            raise SystemExit(
                f"Unknown env '{preflight_env}' for AWS preflight (expected dev/staging/prod)."
            )
        run_secrets_preflight(
            env_name=preflight_env,
            region=args.region,
            profile=args.aws_profile,
            expected_account_id=expected_account_id,
            require_secrets=args.require_secret,
            fail_on_error=True,
        )
    enforced_env = _require_env_flags("prod shadow order status")
    outbound_enabled = _env_truthy(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"))
    allow_network = outbound_enabled or _env_truthy(
        os.environ.get("MW_ALLOW_NETWORK_READS")
    )
    llm_allow_network = allow_network and not args.skip_openai_intent

    if args.retry_diagnostics or args.request_trace:
        os.environ["RICHPANEL_TRACE_ENABLED"] = "true"

    guard = ReadOnlyHttpGuard(
        env_name=env_name,
        richpanel_secret_id=args.richpanel_secret_id,
        shopify_secret_id=args.shopify_secret_id,
    )

    rp_client = GuardedRichpanelClient(
        guard=guard,
        api_key_secret_id=args.richpanel_secret_id,
        dry_run=False,
        read_only=True,
    )
    retry_handler: Optional[_RichpanelRetryDiagnostics] = None
    if args.retry_diagnostics:
        retry_handler = _RichpanelRetryDiagnostics()
        logging.getLogger(
            "richpanel_middleware.integrations.richpanel.client"
        ).addHandler(retry_handler)
    shopify_client = _InstrumentedShopifyClient(
        guard=guard,
        access_token_secret_id=args.shopify_secret_id,
        shop_domain=args.shop_domain,
        allow_network=True,
    )
    shipstation_client = ShipStationClient(allow_network=False)

    explicit_refs = [str(value).strip() for value in (args.ticket_number or [])]
    explicit_refs += [str(value).strip() for value in (args.ticket_id or [])]
    explicit_refs = [value for value in dict.fromkeys(explicit_refs) if value]

    ticket_refs: List[str] = []
    sample_mode = "explicit"
    tickets_requested = 0
    run_warnings: List[str] = []

    if explicit_refs:
        ticket_refs = explicit_refs
        tickets_requested = len(explicit_refs)
        sample_mode = "explicit"
    else:
        try:
            ticket_refs = fetch_recent_ticket_refs(
                rp_client, sample_size=sample_size, list_path=args.ticket_list_path
            )
        except (SystemExit, RichpanelRequestError, SecretLoadError, RichpanelTransportError):
            if args.allow_empty_sample:
                run_warnings.append("ticket_listing_failed")
                LOGGER.warning("Ticket listing failed; continuing with empty sample")
                ticket_refs = []
            else:
                raise
        tickets_requested = sample_size
        sample_mode = "recent"

    if not ticket_refs:
        if args.allow_empty_sample:
            LOGGER.warning("No tickets available for evaluation; continuing")
        else:
            raise SystemExit("No tickets available for evaluation")

    run_id = args.run_id or _build_run_id()
    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc)
    start_time = time.monotonic()
    ticket_results: List[Dict[str, Any]] = []
    failure_modes: Counter[str] = Counter()
    order_status_failure_modes: Counter[str] = Counter()
    stats = Counter()
    trace_entries: List[Dict[str, Any]] = []

    batches: List[List[str]]
    if args.batch_size and args.batch_size > 0:
        batches = [
            ticket_refs[i : i + args.batch_size]
            for i in range(0, len(ticket_refs), args.batch_size)
        ]
    else:
        batches = [ticket_refs]

    for batch_index, batch_refs in enumerate(batches):
        if batch_index and args.batch_delay_seconds:
            time.sleep(args.batch_delay_seconds)
        for ticket_ref in batch_refs:
            ticket_started = time.monotonic()
            redacted_ticket = _redact_identifier(ticket_ref) or "redacted"
            result: Dict[str, Any] = {
                "ticket_id_redacted": redacted_ticket,
                "classification_source": "deterministic_router",
            }
            shopify_calls_before = shopify_client.request_count
            error: Optional[Dict[str, str]] = None
            match_attempted = False
            if _env_truthy(os.environ.get("RICHPANEL_TRACE_ENABLED")):
                rp_client.clear_request_trace()
            try:
                ticket_payload = _fetch_ticket(rp_client, ticket_ref)
                ticket_number, ticket_id = extract_ticket_fields(ticket_payload)
                ticket_id_value = ticket_id or ticket_ref
                if args.skip_conversations:
                    convo_payload = {}
                else:
                    convo_payload = _fetch_conversation(
                        rp_client,
                        ticket_id_value,
                        conversation_id=ticket_payload.get("conversation_id"),
                        conversation_no=ticket_payload.get("conversation_no"),
                    )

                channel_value = _extract_channel(ticket_payload) or _extract_channel(
                    convo_payload
                )
                result["channel"] = _classify_channel(channel_value)
                result["ticket_number_redacted"] = _redact_identifier(ticket_number)
                result["ticket_created_at_redacted"] = _redact_date(
                    ticket_payload.get("created_at") or ticket_payload.get("createdAt")
                )

                order_payload = _build_order_payload(ticket_payload, convo_payload)
                raw_message = _extract_latest_customer_message(
                    ticket_payload, convo_payload
                )
                customer_message = raw_message or "(not provided)"
                order_payload["customer_message"] = customer_message
                order_payload["ticket_id"] = ticket_id_value
                order_payload["conversation_id"] = (
                    ticket_payload.get("conversation_id") or ticket_id_value
                )

                email, name = order_lookup._extract_customer_identity(order_payload)
                order_number = extract_order_number(ticket_payload) or extract_order_number(
                    convo_payload
                )

                result["customer_email_redacted"] = _redact_identifier(email)
                result["customer_name_redacted"] = _redact_identifier(name)
                result["order_number_redacted"] = _redact_identifier(order_number)
                result["message_excerpt_redacted"] = redact_ticket_text(raw_message or "")

                envelope = build_event_envelope(
                    order_payload, source="shadow_order_status"
                )
                routing, routing_artifact = compute_dual_routing(
                    order_payload,
                    conversation_id=envelope.conversation_id,
                    event_id=envelope.event_id,
                    safe_mode=False,
                    automation_enabled=True,
                    allow_network=llm_allow_network,
                    outbound_enabled=outbound_enabled,
                )
                intent_metadata: Dict[str, str] = {}
                if channel_value:
                    intent_metadata["ticket_channel"] = channel_value
                order_status_intent = classify_order_status_intent(
                    customer_message,
                    conversation_id=envelope.conversation_id,
                    event_id=envelope.event_id,
                    safe_mode=False,
                    automation_enabled=True,
                    allow_network=llm_allow_network,
                    outbound_enabled=outbound_enabled,
                    metadata=intent_metadata or None,
                )
                intent_result = order_status_intent.result
                classified_order_status = bool(
                    intent_result.is_order_status if intent_result else False
                )
                if not order_status_intent.llm_called:
                    classified_order_status = routing.intent in ORDER_STATUS_INTENTS
                result["classified_order_status"] = classified_order_status
                result["routing_intent"] = routing.intent
                result["routing_primary_source"] = (
                    routing_artifact.primary_source if routing_artifact else None
                )
                llm_suggestion = (
                    routing_artifact.llm_suggestion
                    if routing_artifact and isinstance(routing_artifact.llm_suggestion, dict)
                    else {}
                )
                routing_llm_called = bool(llm_suggestion.get("llm_called"))
                result["openai_routing"] = {
                    "llm_called": routing_llm_called,
                    "response_id": llm_suggestion.get("response_id"),
                    "response_id_unavailable_reason": llm_suggestion.get(
                        "response_id_unavailable_reason"
                    ),
                    "confidence": llm_suggestion.get("confidence"),
                    "gated_reason": llm_suggestion.get("gated_reason"),
                    "model": llm_suggestion.get("model"),
                }
                result["openai_intent"] = {
                    "llm_called": bool(order_status_intent.llm_called),
                    "response_id": order_status_intent.response_id,
                    "response_id_unavailable_reason": order_status_intent.response_id_unavailable_reason,
                    "confidence": intent_result.confidence if intent_result else None,
                    "gated_reason": order_status_intent.gated_reason,
                    "accepted": order_status_intent.accepted,
                }
                result["classification_source"] = (
                    "openai_intent"
                    if order_status_intent.llm_called
                    else "deterministic_router"
                )

                match_result = "no_match"
                tracking_present = False
                eta_window = None
                order_resolution = None

                force_lookup = bool(args.force_shopify_lookup)
                result["shopify_lookup_forced"] = bool(
                    force_lookup and not classified_order_status
                )
                if classified_order_status or force_lookup:
                    match_attempted = True
                    try:
                        order_summary = lookup_order_summary(
                            envelope,
                            safe_mode=False,
                            automation_enabled=True,
                            allow_network=allow_network,
                            shopify_client=shopify_client,
                            shipstation_client=shipstation_client,
                        )
                    except (ShopifyRequestError, ShopifyTransportError) as exc:
                        error = safe_error(exc)
                        order_summary = {}
                    order_resolution = (
                        order_summary.get("order_resolution")
                        if isinstance(order_summary, dict)
                        else None
                    )
                    tracking_present = _tracking_present(order_summary)
                    if not tracking_present:
                        eta_window = _compute_eta_window(
                            order_summary,
                            ticket_payload.get("created_at")
                            or ticket_payload.get("createdAt"),
                        )

                    shopify_calls_after = shopify_client.request_count
                    shopify_calls = shopify_calls_after - shopify_calls_before
                    match_result = _match_result(
                        order_summary=order_summary,
                        order_number_present=bool(order_number),
                        email_present=bool(email),
                        shopify_calls=shopify_calls,
                        error=error,
                    )
                else:
                    shopify_calls = 0

                result.update(
                    {
                        "match_result": match_result,
                        "tracking_present": tracking_present,
                        "eta_window": eta_window,
                        "match_attempted": match_attempted,
                        "would_auto_reply": bool(
                            classified_order_status
                            and match_result
                            in {"matched_by_order_number", "matched_by_email"}
                            and (tracking_present or eta_window)
                        ),
                        "order_resolution": order_resolution,
                    }
                )
            except SystemExit as exc:
                if args.allow_ticket_fetch_failures and "Ticket lookup failed" in str(exc):
                    error = {"type": "richpanel_error"}
                    result["match_result"] = "error"
                    result["tracking_present"] = False
                    result["eta_window"] = None
                    result["match_attempted"] = match_attempted
                    result["would_auto_reply"] = False
                    result["failure_reason"] = "ticket_fetch_failed"
                    run_warnings.append("ticket_fetch_failed")
                else:
                    raise
            except (RichpanelRequestError, SecretLoadError, RichpanelTransportError) as exc:
                error = safe_error(exc)
                result["match_result"] = "error"
                result["tracking_present"] = False
                result["eta_window"] = None
                result["match_attempted"] = match_attempted
                result["would_auto_reply"] = False
            except ReadOnlyGuardError as exc:
                error = {"type": "read_only_guard"}
                result["match_result"] = "error"
                result["tracking_present"] = False
                result["eta_window"] = None
                result["match_attempted"] = match_attempted
                result["match_attempted"] = match_attempted
                result["would_auto_reply"] = False
                LOGGER.error("Read-only guard blocked request: %s", exc)
            except Exception as exc:
                error = safe_error(exc)
                result["match_result"] = "error"
                result["tracking_present"] = False
                result["eta_window"] = None
                result["match_attempted"] = match_attempted
                result["would_auto_reply"] = False
            finally:
                if error:
                    result["error"] = error
                elapsed = time.monotonic() - ticket_started
                result["elapsed_seconds"] = round(elapsed, 3)
                ticket_results.append(result)

                if _env_truthy(os.environ.get("RICHPANEL_TRACE_ENABLED")):
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

                stats["tickets_scanned"] += 1
                if result.get("classified_order_status"):
                    stats["classified_order_status_true"] += 1
                else:
                    stats["classified_order_status_false"] += 1
                stats[result.get("match_result", "no_match")] += 1
                if result.get("shopify_lookup_forced"):
                    stats["shopify_lookup_forced"] += 1
                if result.get("tracking_present"):
                    stats["tracking_present"] += 1
                if result.get("eta_window"):
                    stats["eta_available"] += 1
                if result.get("error"):
                    stats["errors"] += 1
                if (
                    isinstance(result.get("openai_routing"), dict)
                    and result["openai_routing"].get("llm_called")
                ):
                    stats["openai_routing_called"] += 1
                if (
                    isinstance(result.get("openai_intent"), dict)
                    and result["openai_intent"].get("llm_called")
                ):
                    stats["openai_intent_called"] += 1

                failure_mode = _failure_mode(
                    match_result=result.get("match_result", "no_match"),
                    order_number_present=bool(result.get("order_number_redacted")),
                    email_present=bool(result.get("customer_email_redacted")),
                    error=result.get("error"),
                    order_resolution=(
                        result.get("order_resolution")
                        if isinstance(result.get("order_resolution"), dict)
                        else None
                    ),
                )
                if failure_mode:
                    failure_modes[failure_mode] += 1
                    if result.get("classified_order_status"):
                        order_status_failure_modes[failure_mode] += 1
                if args.throttle_seconds:
                    time.sleep(args.throttle_seconds)

    stats["tickets_requested"] = tickets_requested
    stats["ticket_count"] = len(ticket_results)
    stats["missing_order_number"] = failure_modes.get("missing_order_number", 0)
    stats["missing_email"] = failure_modes.get("missing_email", 0)
    stats["shopify_error"] = failure_modes.get("shopify_error", 0)
    required_stats_keys = [
        "tickets_requested",
        "tickets_scanned",
        "ticket_count",
        "classified_order_status_true",
        "classified_order_status_false",
        "openai_routing_called",
        "openai_intent_called",
        "matched_by_order_number",
        "matched_by_email",
        "no_match",
        "error",
        "tracking_present",
        "eta_available",
        "errors",
        "missing_order_number",
        "missing_email",
        "shopify_error",
        "shopify_lookup_forced",
    ]
    for key in required_stats_keys:
        stats.setdefault(key, 0)

    classification_counts = Counter(
        item.get("classification_source", "unknown") for item in ticket_results
    )
    classification_source = (
        "mixed"
        if len(classification_counts) > 1
        else (next(iter(classification_counts.keys()), "unknown"))
    )
    order_status_rate = None
    if stats.get("ticket_count"):
        order_status_rate = round(
            stats.get("classified_order_status_true", 0)
            / max(stats.get("ticket_count", 1), 1),
            3,
        )

    order_status_results = [
        item for item in ticket_results if item.get("classified_order_status")
    ]
    order_status_count = len(order_status_results)
    match_attempted_count = sum(
        1 for item in order_status_results if item.get("match_attempted")
    )
    matched_by_order_number = sum(
        1
        for item in order_status_results
        if item.get("match_result") == "matched_by_order_number"
    )
    matched_by_email = sum(
        1
        for item in order_status_results
        if item.get("match_result") == "matched_by_email"
    )
    tracking_present_count = sum(
        1 for item in order_status_results if item.get("tracking_present")
    )
    eta_available_count = sum(
        1 for item in order_status_results if item.get("eta_window")
    )
    match_rate_among_order_status = (
        round(
            (matched_by_order_number + matched_by_email)
            / max(order_status_count, 1),
            3,
        )
        if order_status_count
        else None
    )
    tracking_rate = (
        round(tracking_present_count / max(order_status_count, 1), 3)
        if order_status_count
        else None
    )
    no_tracking_count = order_status_count - tracking_present_count
    eta_rate_when_no_tracking = (
        round(eta_available_count / max(no_tracking_count, 1), 3)
        if no_tracking_count > 0
        else None
    )

    failure_mode_list = [
        {"mode": mode, "count": count}
        for mode, count in failure_modes.most_common(5)
    ]
    order_status_failure_mode_list = [
        {"mode": mode, "count": count}
        for mode, count in order_status_failure_modes.most_common(5)
    ]
    request_burst = _summarize_request_burst(trace_entries)
    retry_after_validation = _summarize_retry_after(trace_entries)
    retry_diagnostics: Dict[str, Any] = {}
    if retry_handler is not None:
        retry_diagnostics = _summarize_retry_diagnostics(retry_handler)
        if retry_diagnostics and "richpanel_retries_observed" not in run_warnings:
            run_warnings.append("richpanel_retries_observed")
        logging.getLogger(
            "richpanel_middleware.integrations.richpanel.client"
        ).removeHandler(retry_handler)

    retry_status_counts = {}
    if retry_diagnostics:
        retry_status_counts = retry_diagnostics.get("status_counts") or {}
    retry_429_count = (
        retry_status_counts.get(429)
        or retry_status_counts.get("429")
        or retry_status_counts.get(429.0)
        or 0
    )

    stats_global = {
        "tickets_scanned": stats.get("tickets_scanned", 0),
        "classified_order_status_true": stats.get("classified_order_status_true", 0),
        "classified_order_status_false": stats.get("classified_order_status_false", 0),
        "openai_routing_called": stats.get("openai_routing_called", 0),
        "openai_intent_called": stats.get("openai_intent_called", 0),
        "shopify_lookup_forced": stats.get("shopify_lookup_forced", 0),
        "errors": stats.get("errors", 0),
        "richpanel_retry_total": retry_diagnostics.get("total_retries", 0)
        if retry_diagnostics
        else 0,
        "richpanel_retry_429_count": retry_429_count,
    }
    stats_order_status = {
        "order_status_count": order_status_count,
        "match_attempted_count": match_attempted_count,
        "matched_by_order_number": matched_by_order_number,
        "matched_by_email": matched_by_email,
        "match_rate_among_order_status": match_rate_among_order_status,
        "tracking_present_count": tracking_present_count,
        "tracking_rate": tracking_rate,
        "eta_available_count": eta_available_count,
        "eta_rate_when_no_tracking": eta_rate_when_no_tracking,
    }

    report = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": env_name,
        "env_flags": enforced_env,
        "sample_mode": sample_mode,
        "conversation_mode": "skipped" if args.skip_conversations else "full",
        "ticket_count": len(ticket_results),
        "classification_source": classification_source,
        "classification_source_counts": dict(classification_counts),
        "order_status_rate": order_status_rate,
        "stats_global": stats_global,
        "stats_order_status": stats_order_status,
        "stats": dict(stats),
        "failure_modes": failure_mode_list,
        "order_status_failure_modes": order_status_failure_mode_list,
        "run_warnings": run_warnings,
        "tickets": ticket_results,
        "richpanel_retry_diagnostics": retry_diagnostics or None,
        "richpanel_request_burst": request_burst or None,
        "richpanel_retry_after_validation": retry_after_validation or None,
        "richpanel_identity": _build_identity_block(
            client=rp_client,
            env_name=env_name,
            started_at=started_at,
            duration_seconds=time.monotonic() - start_time,
        ),
        "notes": [
            "Ticket identifiers, names, emails, and order numbers are hashed in structured fields.",
            "Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).",
            "No outbound messages are sent; would_auto_reply is theoretical only.",
        ],
        "run_duration_seconds": round(time.monotonic() - start_time, 3),
    }

    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(_build_markdown_report(report), encoding="utf-8")
    if args.retry_proof_path:
        proof_path = Path(args.retry_proof_path).expanduser().resolve()
        proof_path.parent.mkdir(parents=True, exist_ok=True)
        proof_payload = _build_retry_proof(
            run_id=run_id,
            env_name=env_name,
            retry_diagnostics=retry_diagnostics,
            trace_entries=trace_entries,
        )
        proof_path.write_text(
            json.dumps(proof_payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    LOGGER.info(
        "Report written: %s (tickets=%d)",
        out_json,
        len(ticket_results),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
