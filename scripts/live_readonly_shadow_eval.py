#!/usr/bin/env python3
"""
Live Read-Only Shadow Evaluation

Reads real Richpanel + Shopify data for a single ticket without allowing any writes.
Fails closed via environment guards + GET-only request tracing.
Produces PII-safe JSON artifacts under artifacts/.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

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
LOGGER = logging.getLogger("readonly_shadow_eval")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

PROD_RICHPANEL_BASE_URL = "https://api.richpanel.com"

REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_OUTBOUND_ENABLED": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
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
        self._original_urlopen = original

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

        urllib.request.urlopen = _wrapped_urlopen
        return self

    def stop(self) -> None:
        if self._original_urlopen is not None:
            urllib.request.urlopen = self._original_urlopen
            self._original_urlopen = None

    def assert_get_only(self, *, context: str, trace_path: Path) -> None:
        non_get = [entry for entry in self.entries if entry["method"] != "GET"]
        if non_get:
            raise SystemExit(
                f"Non-GET request detected during {context}. Trace: {trace_path}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": list(self.entries),
            "note": "Captured via urllib.request.urlopen; AWS SDK calls are not included.",
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
            errors.append(f"{path}: {exc}")
            continue
        if resp.dry_run or resp.status_code >= 400:
            errors.append(f"{path}: status {resp.status_code} dry_run={resp.dry_run}")
            continue

        payload = resp.json() or {}
        if isinstance(payload, dict) and isinstance(payload.get("ticket"), dict):
            payload = payload["ticket"]
        payload = payload if isinstance(payload, dict) else {}
        payload["__source_path"] = path
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
    except Exception as exc:
        LOGGER.warning("Conversation fetch failed", exc_info=exc)
        return {}


def _extract_customer_identifiers(ticket: Dict[str, Any], convo: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract and redact customer identifiers without leaking raw PII."""
    sources: list[Dict[str, Any]] = []
    for candidate in (ticket, convo):
        if isinstance(candidate, dict):
            sources.append(candidate)
            profile = candidate.get("customer") or candidate.get("customer_profile")
            if isinstance(profile, dict):
                sources.append(profile)

    email = None
    phone = None
    name = None
    for source in sources:
        email = email or source.get("email")
        phone = phone or source.get("phone") or source.get("phone_number")
        name = name or source.get("name") or source.get("customer_name")

    return {
        "email": _redact_identifier(email),
        "phone": _redact_identifier(phone),
        "name": _redact_identifier(name),
    }


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


def _build_artifact_path(ticket_id: str) -> Path:
    safe_id = _fingerprint(ticket_id)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "readonly_shadow"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{timestamp}_{safe_id}.json"


def _build_trace_path() -> Path:
    out_dir = ROOT / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "prod_readonly_shadow_eval_http_trace.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live read-only shadow evaluation.")
    parser.add_argument(
        "--ticket-id",
        required=True,
        help="Richpanel ticket/conversation id to evaluate",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Optional override for rp-mw/<env>/richpanel/api_key secret id",
    )
    parser.add_argument(
        "--shop-domain",
        help="Optional Shopify shop domain override (defaults to env)",
    )
    args = parser.parse_args()

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
    trace = _HttpTrace().capture()
    try:
        rp_client = _build_richpanel_client(
            richpanel_secret=args.richpanel_secret_id,
            base_url=richpanel_base_url,
        )

        ticket_payload = _fetch_ticket(rp_client, args.ticket_id)
        convo_payload = _fetch_conversation(rp_client, args.ticket_id)
        order_payload = _extract_order_payload(ticket_payload, convo_payload)
        customer_ids = _extract_customer_identifiers(ticket_payload, convo_payload)

        customer_message = extract_customer_message(
            order_payload, default="(not provided)"
        )
        event_payload = dict(order_payload)
        event_payload.update(
            {
                "ticket_id": args.ticket_id,
                "conversation_id": args.ticket_id,
                "customer_message": customer_message,
            }
        )

        envelope = normalize_event({"payload": event_payload})
        # Keep outbound disabled to avoid any outbound messaging/LLM calls.
        plan = plan_actions(
            envelope,
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=False,
        )

        order_action = next(
            (a for a in plan.actions if a.get("type") == "order_status_draft_reply"),
            None,
        )
        parameters = (
            order_action.get("parameters", {}) if isinstance(order_action, dict) else {}
        )
        order_summary = (
            parameters.get("order_summary") if isinstance(parameters, dict) else {}
        )
        delivery_estimate = (
            parameters.get("delivery_estimate") if isinstance(parameters, dict) else None
        )
        tracking_found = _tracking_present(order_summary or {})
    finally:
        trace.stop()
        trace_path = _build_trace_path()
        with trace_path.open("w", encoding="utf-8") as fh:
            json.dump(trace.to_dict(), fh, ensure_ascii=False, indent=2)
        trace.assert_get_only(
            context="read-only shadow evaluation", trace_path=trace_path
        )

    artifact = {
        "ticket_id_redacted": _redact_identifier(args.ticket_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env_flags": enforced_env,
        "prod_target": is_prod_target,
        "http_trace_path": str(_build_trace_path()),
        "customer": customer_ids,
        "routing": {
            "intent": getattr(plan.routing, "intent", None),
            "department": getattr(plan.routing, "department", None),
            "reason": getattr(plan.routing, "reason", None),
            "mode": plan.mode,
            "reasons": plan.reasons,
        },
        "order": {
            "order_id_redacted": _redact_identifier(str(order_summary.get("order_id", "")))
            if isinstance(order_summary, dict)
            else None,
            "tracking_found": tracking_found,
            "eta_window": delivery_estimate.get("eta_human") if isinstance(delivery_estimate, dict) else None,
            "delivery_estimate": {
                "window_min_days": delivery_estimate.get("window_min_days"),
                "window_max_days": delivery_estimate.get("window_max_days"),
                "bucket": delivery_estimate.get("bucket"),
                "is_late": delivery_estimate.get("is_late"),
            }
            if isinstance(delivery_estimate, dict)
            else None,
        },
        "plan_preview": {
            "actions": [a.get("type") for a in plan.actions],
            "has_draft_reply": bool(parameters.get("draft_reply")) if isinstance(parameters, dict) else False,
        },
    }

    out_path = _build_artifact_path(args.ticket_id)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(artifact, fh, ensure_ascii=False, indent=2)

    LOGGER.info("Planned response (PII-safe preview):")
    LOGGER.info(json.dumps(artifact["plan_preview"], indent=2))
    LOGGER.info("Artifact written to %s", out_path)
    LOGGER.info("HTTP trace written to %s", _build_trace_path())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
