#!/usr/bin/env python3
"""
Live Read-Only Shadow Evaluation

Reads real Richpanel + Shopify data for a small ticket sample without allowing any writes.
Fails closed via environment guards + GET-only request tracing.
Produces PII-safe JSON + markdown artifacts under artifacts/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.pipeline import plan_actions, normalize_event  # type: ignore
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
)
from readonly_shadow_utils import (
    fetch_recent_ticket_refs as _fetch_recent_ticket_refs,
    safe_error as _safe_error,
)
LOGGER = logging.getLogger("readonly_shadow_eval")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("richpanel_middleware").setLevel(logging.WARNING)
logging.getLogger("integrations").setLevel(logging.WARNING)

PROD_RICHPANEL_BASE_URL = "https://api.richpanel.com"

REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_OUTBOUND_ENABLED": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
}

ALLOWED_PROD_ENVS = {"prod", "production"}
DEFAULT_SAMPLE_SIZE = 10


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
    *, allow_network: Optional[bool], shop_domain: Optional[str]
) -> ShopifyClient:
    return ShopifyClient(shop_domain=shop_domain, allow_network=allow_network)


def _probe_shopify(*, shop_domain: Optional[str]) -> Dict[str, Any]:
    client = _build_shopify_client(allow_network=None, shop_domain=shop_domain)
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


class _HttpTrace:
    _original_urlopen: Any

    def __init__(self) -> None:
        self.entries: list[Dict[str, str]] = []
        self._original_urlopen = None

    def record(self, method: str, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        path = _redact_path(parsed.path)
        service = "unknown"
        hostname = parsed.hostname or ""
        if hostname.endswith("richpanel.com"):
            service = "richpanel"
        elif hostname.endswith("myshopify.com"):
            service = "shopify"
        elif hostname.endswith("shipstation.com"):
            service = "shipstation"
        self.entries.append(
            {"method": method.upper(), "path": path, "service": service}
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
        return self

    def stop(self) -> None:
        if self._original_urlopen is not None:
            urllib.request.urlopen = self._original_urlopen  # type: ignore
            self._original_urlopen = None

    def assert_get_only(self, *, context: str, trace_path: Path) -> None:
        allowed = {"GET", "HEAD"}
        non_allowed = [entry for entry in self.entries if entry["method"] not in allowed]
        if non_allowed:
            raise SystemExit(
                f"Non-GET request detected during {context}. Trace: {trace_path}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": list(self.entries),
            "note": "Captured via urllib.request.urlopen; AWS SDK calls are not included.",
        }


def _summarize_trace(trace: _HttpTrace) -> Dict[str, Any]:
    methods = Counter(entry.get("method") for entry in trace.entries)
    services = Counter(entry.get("service") for entry in trace.entries)
    return {
        "total_requests": len(trace.entries),
        "methods": dict(methods),
        "services": dict(services),
        "allowed_methods_only": all(
            entry.get("method") in {"GET", "HEAD"} for entry in trace.entries
        ),
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


def _fetch_conversation(client: RichpanelClient, ticket_id: str) -> Dict[str, Any]:
    """Best-effort conversation read; tolerates failures."""
    encoded = urllib.parse.quote(ticket_id, safe="")
    try:
        resp = client.request(
            "GET",
            f"/api/v1/conversations/{encoded}",
            dry_run=False,
            log_body_excerpt=False,
        )
        if resp.dry_run or resp.status_code >= 400:
            LOGGER.warning(
                "Conversation fetch skipped",
                extra={"status": resp.status_code, "dry_run": resp.dry_run},
            )
            return {}
        payload = resp.json()
        return payload if isinstance(payload, dict) else {}
    except Exception:
        LOGGER.warning("Conversation fetch failed")
        return {}


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
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of recent tickets to sample when --ticket-id is not provided",
    )
    parser.add_argument(
        "--ticket-list-path",
        default="/v1/tickets",
        help="Richpanel API path for ticket listing (default: /v1/tickets)",
    )
    parser.add_argument(
        "--allow-non-prod",
        action="store_true",
        help="Allow non-prod runs for local tests",
    )
    parser.add_argument(
        "--run-id",
        help="Optional run id override for artifact filenames",
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
    args = parser.parse_args()

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

    run_id = args.run_id or _build_run_id()
    report_path, report_md_path, trace_path = _build_report_paths(run_id)

    trace = _HttpTrace().capture()
    had_errors = False
    ticket_results: List[Dict[str, Any]] = []
    ticket_refs: List[str] = []
    sample_mode = "explicit"
    tickets_requested = 0
    shopify_probe: Dict[str, Any] = {"enabled": bool(args.shopify_probe)}
    try:
        rp_client = _build_richpanel_client(
            richpanel_secret=args.richpanel_secret_id,
            base_url=richpanel_base_url,
        )

        if args.shopify_probe:
            try:
                probe = _probe_shopify(shop_domain=args.shop_domain)
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
            ticket_refs = _fetch_recent_ticket_refs(
                rp_client,
                sample_size=args.sample_size,
                list_path=args.ticket_list_path,
            )
            tickets_requested = args.sample_size
            sample_mode = "recent"

        if not ticket_refs:
            raise SystemExit("No tickets available for evaluation")
        if len(ticket_refs) < tickets_requested:
            LOGGER.warning(
                "Sample size reduced: requested %d got %d",
                tickets_requested,
                len(ticket_refs),
            )

        for ticket_ref in ticket_refs:
            redacted = _redact_identifier(ticket_ref) or "redacted"
            result: Dict[str, Any] = {"ticket_id_redacted": redacted}
            try:
                ticket_payload = _fetch_ticket(rp_client, ticket_ref)
                convo_payload = _fetch_conversation(rp_client, ticket_ref)
                order_payload = _extract_order_payload(ticket_payload, convo_payload)

                customer_message = extract_customer_message(
                    order_payload, default="(not provided)"
                )
                event_payload = dict(order_payload)
                event_payload.update(
                    {
                        "ticket_id": ticket_ref,
                        "conversation_id": ticket_ref,
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
                    parameters.get("order_summary") if isinstance(parameters, dict) else {}
                )
                delivery_estimate = (
                    parameters.get("delivery_estimate")
                    if isinstance(parameters, dict)
                    else None
                )
                tracking_found = _tracking_present(order_summary or {})
                eta_available = _delivery_estimate_present(delivery_estimate)

                result.update(
                    {
                        "order_status_candidate": bool(order_action),
                        "order_matched": bool(order_summary),
                        "tracking_found": tracking_found,
                        "eta_available": eta_available,
                    }
                )
            except SystemExit:
                raise
            except Exception as exc:
                had_errors = True
                result["error"] = _safe_error(exc)
            ticket_results.append(result)
    finally:
        trace.stop()
        with trace_path.open("w", encoding="utf-8") as fh:
            json.dump(trace.to_dict(), fh, ensure_ascii=False, indent=2)
        trace.assert_get_only(
            context="read-only shadow evaluation", trace_path=trace_path
        )

    trace_summary = _summarize_trace(trace)
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
        "errors": sum(1 for item in ticket_results if item.get("error")),
    }

    report = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": env_name,
        "env_flags": enforced_env,
        "prod_target": is_prod_target,
        "sample_mode": sample_mode,
        "counts": counts,
        "shopify_probe": shopify_probe,
        "tickets": ticket_results,
        "http_trace_path": str(trace_path),
        "http_trace_summary": trace_summary,
        "notes": [
            "Ticket identifiers are hashed.",
            "No message bodies or customer identifiers are stored.",
            "HTTP trace captures urllib.request calls; AWS SDK calls are not included.",
        ],
    }

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_lines = [
        "# Live Read-Only Shadow Eval Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Generated (UTC): {report['timestamp']}",
        f"- Environment: `{env_name}`",
        f"- Sample mode: `{sample_mode}`",
        f"- Tickets requested: {counts['tickets_requested']}",
        f"- Tickets scanned: {counts['tickets_scanned']}",
        f"- Orders matched: {counts['orders_matched']}",
        f"- Tracking found: {counts['tracking_found']}",
        f"- ETA available: {counts['eta_available']}",
        f"- Errors: {counts['errors']}",
        f"- Shopify probe enabled: {shopify_probe['enabled']}",
        f"- Shopify probe ok: {shopify_probe.get('ok')}",
        f"- Shopify probe status: {shopify_probe.get('status_code')}",
        "",
        "## HTTP Trace Summary",
        f"- Total requests: {trace_summary['total_requests']}",
        f"- Methods: {json.dumps(trace_summary['methods'], sort_keys=True)}",
        f"- Services: {json.dumps(trace_summary['services'], sort_keys=True)}",
        f"- Allowed methods only: {trace_summary['allowed_methods_only']}",
        f"- Trace path: `{trace_path}`",
        "",
        "## Notes",
        "- Ticket identifiers are hashed in the JSON report.",
        "- No message bodies or customer identifiers are stored.",
        "- HTTP trace captures urllib.request calls; AWS SDK calls are not included.",
    ]
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
    LOGGER.info("HTTP trace written to %s", trace_path)
    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
