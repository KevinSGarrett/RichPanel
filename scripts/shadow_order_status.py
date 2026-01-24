#!/usr/bin/env python3
"""
Shadow-mode validation harness for Order Status automation.

Reads live Richpanel + Shopify data in read-only mode, runs routing + ETA logic,
and writes a PII-safe JSON proof artifact. No side effects permitted.
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
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.delivery_estimate import (  # type: ignore
    build_no_tracking_reply,
    build_tracking_reply,
    compute_delivery_estimate,
)
from richpanel_middleware.automation.llm_reply_rewriter import (  # type: ignore
    ReplyRewriteResult,
    rewrite_reply,
)
from richpanel_middleware.automation.llm_routing import (  # type: ignore
    _to_bool,
    compute_dual_routing,
)
from richpanel_middleware.automation.router import (  # type: ignore
    extract_customer_message,
)
from richpanel_middleware.commerce.order_lookup import (  # type: ignore
    SHOPIFY_ORDER_FIELDS,
    _baseline_summary,
    _extract_shopify_fields,
    _merge_summary,
    _order_summary_from_payload,
)
from richpanel_middleware.ingest.envelope import (  # type: ignore
    EventEnvelope,
    normalize_envelope,
)
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

LOGGER = logging.getLogger("shadow_order_status")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("richpanel_middleware").setLevel(logging.WARNING)
logging.getLogger("integrations").setLevel(logging.WARNING)

ORDER_STATUS_INTENTS = {"order_status_tracking", "shipping_delay_not_shipped"}
ALLOWED_ENVS = {"staging", "prod"}


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


def _require_env_flag(key: str, expected: str, *, context: str) -> None:
    actual = os.environ.get(key)
    if actual is None:
        raise SystemExit(f"{key} must be {expected} for {context} (unset)")
    if str(actual).strip().lower() != expected:
        raise SystemExit(f"{key} must be {expected} for {context} (found {actual})")


def _resolve_env_name() -> str:
    value = os.environ.get("RICHPANEL_ENV") or os.environ.get("RICH_PANEL_ENV")
    if value is None:
        raise SystemExit(
            "RICHPANEL_ENV must be set to 'staging' or 'prod' for shadow order status"
        )
    normalized = str(value).strip().lower()
    if not normalized:
        raise SystemExit(
            "RICHPANEL_ENV must be set to 'staging' or 'prod' for shadow order status"
        )
    return normalized


def _resolve_shopify_secret_id(env_name: str) -> str:
    if os.environ.get("SHOPIFY_ACCESS_TOKEN_OVERRIDE"):
        raise SystemExit(
            "SHOPIFY_ACCESS_TOKEN_OVERRIDE is not allowed in shadow mode; use Secrets Manager"
        )
    override = os.environ.get("SHOPIFY_ACCESS_TOKEN_SECRET_ID")
    if override:
        lowered = override.lower()
        if "/shopify/admin_api_token" in lowered or "/shopify/access_token" in lowered:
            return override
        raise SystemExit(
            "SHOPIFY_ACCESS_TOKEN_SECRET_ID must reference a Shopify admin_api_token/access_token secret"
        )
    return f"rp-mw/{env_name}/shopify/admin_api_token"


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
        "admin",
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
        elif hostname.endswith("openai.com"):
            service = "openai"
        elif hostname.endswith("anthropic.com"):
            service = "anthropic"
        self.entries.append(
            {"method": method.upper(), "path": path, "service": service}
        )

    def capture(self) -> "_HttpTrace":
        original = urllib.request.urlopen
        self._original_urlopen = original  # type: ignore

        def _wrapped_urlopen(req, *args, **kwargs):
            try:
                method = req.get_method() if hasattr(req, "get_method") else "GET"
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

    def assert_read_only(
        self, *, allow_openai: bool, trace_path: Path
    ) -> None:
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
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": list(self.entries),
            "note": "Captured via urllib.request.urlopen; AWS SDK calls are not included.",
        }


def _resolve_network_flags() -> Tuple[bool, bool]:
    outbound_enabled = _to_bool(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"), False)
    allow_network = outbound_enabled or _to_bool(
        os.environ.get("MW_ALLOW_NETWORK_READS"), False
    )
    return allow_network, outbound_enabled


def _require_readonly_guards(*, confirm_live_readonly: bool) -> str:
    _require_env_flag(
        "RICHPANEL_READ_ONLY", "true", context="shadow order status"
    )
    _require_env_flag(
        "RICHPANEL_WRITE_DISABLED", "true", context="shadow order status"
    )
    env_name = _resolve_env_name()
    if env_name not in ALLOWED_ENVS:
        raise SystemExit(
            f"RICHPANEL_ENV must be one of {sorted(ALLOWED_ENVS)} (found {env_name})"
        )
    if not confirm_live_readonly:
        raise SystemExit(
            "--confirm-live-readonly is required for non-sandbox environments"
        )

    # Ensure downstream integrations resolve the same environment.
    if not os.environ.get("RICHPANEL_ENV"):
        os.environ["RICHPANEL_ENV"] = env_name

    allow_network, _ = _resolve_network_flags()
    if not allow_network:
        raise SystemExit(
            "MW_ALLOW_NETWORK_READS or RICHPANEL_OUTBOUND_ENABLED must be true "
            "to allow read-only network access"
        )
    return env_name


def _build_richpanel_client() -> RichpanelClient:
    return RichpanelClient(dry_run=False, read_only=True)


def _build_shopify_client(*, allow_network: bool, env_name: str) -> ShopifyClient:
    secret_id = _resolve_shopify_secret_id(env_name)
    return ShopifyClient(
        allow_network=allow_network, access_token_secret_id=secret_id
    )


def _build_trace_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "shadow_order_status"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"http_trace_{timestamp}.json"


def _fetch_ticket(client: RichpanelClient, ticket_ref: str) -> Dict[str, Any]:
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
    raise RuntimeError(
        f"Ticket lookup failed for {redacted_ref}: {'; '.join(errors)}"
    )


def _fetch_conversation(
    client: RichpanelClient,
    ticket_id: str,
    *,
    conversation_id: Optional[str] = None,
    conversation_no: Optional[object] = None,
) -> Dict[str, Any]:
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
    text = extract_customer_message(convo, default="")
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


def _extract_customer_presence(
    ticket: Dict[str, Any], convo: Dict[str, Any]
) -> Dict[str, bool]:
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
    address = None
    for source in sources:
        email = email or source.get("email")
        phone = phone or source.get("phone") or source.get("phone_number")
        name = name or source.get("name") or source.get("customer_name")
        address = address or source.get("address") or source.get("shipping_address")
        address = address or source.get("billing_address")

    return {
        "email_present": bool(email),
        "phone_present": bool(phone),
        "name_present": bool(name),
        "address_present": bool(address),
    }


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


def _lookup_order_summary_payload_first(
    envelope: EventEnvelope,
    *,
    allow_network: bool,
    shopify_client: ShopifyClient,
) -> Tuple[Dict[str, Any], str]:
    baseline = _baseline_summary(envelope)
    payload_summary = _order_summary_from_payload(envelope.payload)
    if payload_summary:
        return _merge_summary(baseline, payload_summary), "payload"
    if not allow_network:
        return baseline, "baseline"
    order_id = baseline.get("order_id") or baseline.get("id")
    if not order_id or str(order_id).strip().lower() in {"unknown"}:
        return baseline, "skipped_missing_order_id"

    try:
        response = shopify_client.get_order(
            str(order_id),
            fields=SHOPIFY_ORDER_FIELDS,
            dry_run=not allow_network,
            safe_mode=False,
            automation_enabled=True,
        )
    except ShopifyRequestError:
        return baseline, "baseline"

    if response.dry_run or response.status_code >= 400:
        return baseline, "baseline"

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

    shopify_summary = _extract_shopify_fields(payload)
    if shopify_summary:
        return _merge_summary(baseline, shopify_summary), "shopify"
    return baseline, "baseline"


def _build_openai_evidence(rewrite_result: ReplyRewriteResult) -> Dict[str, Any]:
    return {
        "rewrite_attempted": bool(rewrite_result.llm_called),
        "rewrite_applied": bool(rewrite_result.rewritten),
        "model": rewrite_result.model,
        "response_id": rewrite_result.response_id,
        "response_id_unavailable_reason": rewrite_result.response_id_unavailable_reason,
        "reason": rewrite_result.reason,
    }


def _build_event_envelope(payload: Dict[str, Any], *, ticket_id: str) -> EventEnvelope:
    return normalize_envelope(
        {
            "event_id": f"shadow-order-status:{ticket_id}",
            "conversation_id": ticket_id,
            "payload": payload,
            "source": "shadow_order_status",
        }
    )


def _build_route_info(
    routing: Any, routing_artifact: Any
) -> Dict[str, Optional[Any]]:
    llm = getattr(routing_artifact, "llm_suggestion", None) if routing_artifact else None
    if not isinstance(llm, dict):
        llm = {}
    confidence = llm.get("confidence")
    return {
        "intent": getattr(routing, "intent", None),
        "department": getattr(routing, "department", None),
        "reason": getattr(routing, "reason", None),
        "primary_source": getattr(routing_artifact, "primary_source", None),
        "confidence": confidence,
        "llm_model": llm.get("model"),
        "llm_response_id": llm.get("response_id"),
        "llm_gated_reason": llm.get("gated_reason"),
    }


def run_ticket(
    ticket_id: str,
    *,
    richpanel_client: RichpanelClient,
    shopify_client: ShopifyClient,
    allow_network: bool,
    outbound_enabled: bool,
    rewrite_enabled: bool,
) -> Dict[str, Any]:
    ticket_redacted = _redact_identifier(ticket_id) or "redacted"
    ticket = _fetch_ticket(richpanel_client, ticket_id)
    ticket_id_value = str(ticket.get("id") or ticket_id).strip()
    convo = _fetch_conversation(
        richpanel_client,
        ticket_id_value,
        conversation_id=ticket.get("conversation_id"),
        conversation_no=ticket.get("conversation_no"),
    )
    customer_message = _extract_latest_customer_message(ticket, convo) or "(not provided)"
    payload = _extract_order_payload(ticket, convo)
    payload["ticket_id"] = ticket_id
    payload["conversation_id"] = ticket.get("conversation_id") or ticket_id_value
    payload["customer_message"] = customer_message

    envelope = _build_event_envelope(payload, ticket_id=ticket_id)
    routing, routing_artifact = compute_dual_routing(
        payload,
        conversation_id=envelope.conversation_id,
        event_id=envelope.event_id,
        safe_mode=False,
        automation_enabled=True,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
    )

    route_info = _build_route_info(routing, routing_artifact)
    intent = getattr(routing, "intent", None) if routing else None
    is_order_status = intent in ORDER_STATUS_INTENTS

    result: Dict[str, Any] = {
        "ticket_id_redacted": ticket_redacted,
        "routing": route_info,
        "customer_presence": _extract_customer_presence(ticket, convo),
        "order_status": {
            "is_order_status": is_order_status,
        },
    }

    if not is_order_status:
        result["order_status"].update(
            {
                "skipped_reason": "route_not_order_status",
                "order_summary_found": False,
                "tracking_present": False,
                "eta_window": None,
            }
        )
        return result

    order_summary, summary_source = _lookup_order_summary_payload_first(
        envelope, allow_network=allow_network, shopify_client=shopify_client
    )
    skipped_missing_order_id = summary_source == "skipped_missing_order_id"
    tracking_present = _tracking_present(order_summary)
    order_summary_found = summary_source in {"payload", "shopify"}

    ticket_created_at = (
        payload.get("ticket_created_at")
        or payload.get("created_at")
        or envelope.received_at
    )
    delivery_estimate = None
    draft_reply_type = None
    draft_reply = build_tracking_reply(order_summary)
    if draft_reply:
        draft_reply_type = "tracking"
    if not draft_reply:
        order_created_at = (
            order_summary.get("created_at")
            or order_summary.get("order_created_at")
            or payload.get("order_created_at")
            or payload.get("created_at")
        )
        shipping_method = (
            order_summary.get("shipping_method")
            or order_summary.get("shipping_method_name")
            or payload.get("shipping_method")
            or payload.get("shipping_method_name")
        )
        delivery_estimate = compute_delivery_estimate(
            order_created_at, shipping_method, ticket_created_at
        )
        draft_reply = build_no_tracking_reply(
            order_summary,
            inquiry_date=ticket_created_at,
            delivery_estimate=delivery_estimate,
        )
        if draft_reply:
            draft_reply_type = "no_tracking"

    openai_evidence = None
    if rewrite_enabled and draft_reply and draft_reply.get("body"):
        rewrite_result = rewrite_reply(
            draft_reply.get("body") or "",
            conversation_id=envelope.conversation_id,
            event_id=envelope.event_id,
            safe_mode=False,
            automation_enabled=True,
            allow_network=allow_network,
            outbound_enabled=outbound_enabled,
            rewrite_enabled=True,
        )
        openai_evidence = _build_openai_evidence(rewrite_result)

    result["order_status"].update(
        {
            "order_summary_found": order_summary_found,
            "order_summary_source": summary_source,
            "lookup_status": "SKIPPED" if skipped_missing_order_id else "OK",
            "skipped_reason": "missing_order_id" if skipped_missing_order_id else None,
            "tracking_present": tracking_present,
            "eta_window": {
                "window_min_days": delivery_estimate.get("window_min_days"),
                "window_max_days": delivery_estimate.get("window_max_days"),
                "bucket": delivery_estimate.get("bucket"),
                "is_late": delivery_estimate.get("is_late"),
                "eta_human": delivery_estimate.get("eta_human"),
            }
            if isinstance(delivery_estimate, dict)
            else None,
            "draft_reply_generated": bool(draft_reply),
            "draft_reply_type": draft_reply_type,
        }
    )

    if openai_evidence:
        result["order_status"]["openai_rewrite"] = openai_evidence

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Shadow-mode order status validation (read-only)."
    )
    parser.add_argument(
        "--ticket-id",
        action="append",
        help="Richpanel ticket or conversation id (repeatable)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=0,
        help="Number of recent tickets to sample when --ticket-id is not provided",
    )
    parser.add_argument(
        "--ticket-list-path",
        default="/v1/tickets",
        help="Richpanel API path for ticket listing (default: /v1/tickets)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output JSON path",
    )
    parser.add_argument(
        "--confirm-live-readonly",
        action="store_true",
        help="Required acknowledgment for staging/prod reads",
    )
    parser.add_argument(
        "--max-tickets",
        type=int,
        default=10,
        help="Safety limit on number of tickets",
    )
    args = parser.parse_args()

    env_name = _require_readonly_guards(
        confirm_live_readonly=args.confirm_live_readonly
    )
    if args.max_tickets < 1:
        raise SystemExit("--max-tickets must be >= 1")

    allow_network, outbound_enabled = _resolve_network_flags()
    rewrite_enabled = _to_bool(os.environ.get("OPENAI_REPLY_REWRITE_ENABLED"), False)
    openai_allow_network = _to_bool(os.environ.get("OPENAI_ALLOW_NETWORK"), False)
    allow_openai = openai_allow_network and outbound_enabled

    richpanel_client = _build_richpanel_client()
    shopify_client = _build_shopify_client(
        allow_network=allow_network, env_name=env_name
    )
    deduped: List[str] = []
    sample_mode = "explicit"
    tickets_requested = 0

    trace_path = _build_trace_path()
    trace = _HttpTrace().capture()
    try:
        results: List[Dict[str, Any]] = []
        had_errors = False
        ticket_ids = [str(value).strip() for value in args.ticket_id or []]
        deduped = [value for value in dict.fromkeys(ticket_ids) if value]
        if not deduped:
            if args.sample_size < 1:
                raise SystemExit(
                    "At least one --ticket-id or a positive --sample-size is required"
                )
            if args.sample_size > args.max_tickets:
                raise SystemExit(
                    f"--sample-size must be <= --max-tickets ({args.max_tickets})"
                )
            tickets_requested = args.sample_size
            sample_mode = "recent"
            deduped = _fetch_recent_ticket_refs(
                richpanel_client,
                sample_size=args.sample_size,
                list_path=args.ticket_list_path,
            )
        else:
            tickets_requested = len(deduped)
            sample_mode = "explicit"
        if not deduped:
            raise SystemExit("No tickets available for evaluation")
        if len(deduped) > args.max_tickets:
            raise SystemExit(
                f"Refusing to process {len(deduped)} tickets (max {args.max_tickets})"
            )
        if len(deduped) < tickets_requested:
            LOGGER.warning(
                "Sample size reduced: requested %d got %d",
                tickets_requested,
                len(deduped),
            )

        for ticket_id in deduped:
            redacted = _redact_identifier(ticket_id) or "redacted"
            LOGGER.info("Processing ticket %s", redacted)
            try:
                result = run_ticket(
                    ticket_id,
                    richpanel_client=richpanel_client,
                    shopify_client=shopify_client,
                    allow_network=allow_network,
                    outbound_enabled=outbound_enabled,
                    rewrite_enabled=rewrite_enabled,
                )
            except SystemExit:
                raise
            except Exception as exc:
                had_errors = True
                result = {
                    "ticket_id_redacted": _redact_identifier(ticket_id) or "redacted",
                    "error": _safe_error(exc),
                }
            results.append(result)
    finally:
        trace.stop()
        with trace_path.open("w", encoding="utf-8") as handle:
            json.dump(trace.to_dict(), handle, ensure_ascii=False, indent=2)
        trace.assert_read_only(allow_openai=allow_openai, trace_path=trace_path)

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {
        "tickets_requested": tickets_requested,
        "tickets_selected": len(deduped),
        "tickets_scanned": len(results),
        "order_status_candidates": sum(
            1
            for item in results
            if item.get("order_status", {}).get("is_order_status")
        ),
        "orders_matched": sum(
            1
            for item in results
            if item.get("order_status", {}).get("order_summary_found")
        ),
        "tracking_found": sum(
            1
            for item in results
            if item.get("order_status", {}).get("tracking_present")
        ),
        "eta_available": sum(
            1
            for item in results
            if item.get("order_status", {}).get("eta_window")
        ),
        "errors": sum(1 for item in results if item.get("error")),
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": env_name,
        "sample_mode": sample_mode,
        "counts": counts,
        "http_trace_path": str(trace_path),
        "tickets": results,
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    LOGGER.info("Wrote PII-safe output to %s", out_path)
    LOGGER.info("HTTP trace written to %s", trace_path)
    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
