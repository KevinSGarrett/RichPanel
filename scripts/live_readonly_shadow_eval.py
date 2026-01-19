#!/usr/bin/env python3
"""
Live Read-Only Shadow Evaluation

Reads real Richpanel + Shopify data for a single ticket without allowing any writes.
Fails closed via environment enforcement + explicit Richpanel write-block self-check.
Produces a PII-safe JSON artifact under artifacts/readonly_shadow/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import urllib.parse
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
    RichpanelWriteDisabledError,
    SecretLoadError,
    TransportError,
)
LOGGER = logging.getLogger("readonly_shadow_eval")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_OUTBOUND_ENABLED": "false",
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


def _enforce_required_env() -> Dict[str, str]:
    """Force the required read-only env settings (fail closed if drift is detected)."""
    applied: Dict[str, str] = {}
    for key, expected in REQUIRED_FLAGS.items():
        os.environ[key] = expected
        applied[key] = expected
        actual = os.environ.get(key, "").lower()
        if actual != expected:
            raise SystemExit(f"{key} must be {expected} (found {actual})")
    return applied


def _build_richpanel_client(*, richpanel_secret: Optional[str]) -> RichpanelClient:
    return RichpanelClient(
        api_key_secret_id=richpanel_secret,
        dry_run=False,  # allow GETs; writes are still blocked by RICHPANEL_WRITE_DISABLED
    )


def _assert_write_blocked(client: RichpanelClient) -> None:
    """Attempt a known write path and assert it is blocked."""
    try:
        client.request(
            "PUT",
            "/v1/tickets/readonly-proof/add-tags",
            json_body={"tags": ["readonly-proof"]},
            dry_run=False,
        )
    except RichpanelWriteDisabledError:
        LOGGER.info("Write block self-check: PASSED (RichpanelWriteDisabledError raised)")
        return
    raise SystemExit(
        "Write block self-check FAILED: RichpanelWriteDisabledError was not raised."
    )


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
    raise SystemExit(f"Ticket lookup failed for {ticket_ref}: {'; '.join(errors)}")


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
    safe_id = "".join(ch for ch in ticket_id if ch.isalnum() or ch in ("-", "_"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "readonly_shadow"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{timestamp}_{safe_id}.json"


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

    enforced_env = _enforce_required_env()
    if args.shop_domain:
        os.environ["SHOPIFY_SHOP_DOMAIN"] = args.shop_domain
    rp_client = _build_richpanel_client(richpanel_secret=args.richpanel_secret_id)

    _assert_write_blocked(rp_client)

    ticket_payload = _fetch_ticket(rp_client, args.ticket_id)
    convo_payload = _fetch_conversation(rp_client, args.ticket_id)
    order_payload = _extract_order_payload(ticket_payload, convo_payload)
    customer_ids = _extract_customer_identifiers(ticket_payload, convo_payload)

    customer_message = extract_customer_message(order_payload, default="(not provided)")
    event_payload = dict(order_payload)
    event_payload.update(
        {
            "ticket_id": args.ticket_id,
            "conversation_id": args.ticket_id,
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
        (a for a in plan.actions if a.get("type") == "order_status_draft_reply"), None
    )
    parameters = order_action.get("parameters", {}) if isinstance(order_action, dict) else {}
    order_summary = parameters.get("order_summary") if isinstance(parameters, dict) else {}
    delivery_estimate = parameters.get("delivery_estimate") if isinstance(parameters, dict) else None
    tracking_found = _tracking_present(order_summary or {})

    artifact = {
        "ticket_id": args.ticket_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env_flags": enforced_env,
        "write_block_self_check": True,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
