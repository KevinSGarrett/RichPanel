from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import time
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from integrations.common import PRODUCTION_ENVIRONMENTS, resolve_env_name, _to_bool
from richpanel_middleware.automation.delivery_estimate import (
    build_no_tracking_reply,
    build_tracking_reply,
    compute_delivery_estimate,
    normalize_shipping_method,
)
from richpanel_middleware.automation.router import (
    RoutingDecision,
    extract_customer_message,
)
from richpanel_middleware.automation.llm_routing import (
    RoutingArtifact,
    compute_dual_routing,
)
from richpanel_middleware.automation.llm_reply_rewriter import (
    ReplyRewriteResult,
    rewrite_reply,
)
from richpanel_middleware.automation.order_status_intent import (
    OrderStatusIntentArtifact,
    classify_order_status_intent,
)
from richpanel_middleware.automation.order_status_prompts import (
    OrderStatusReplyContext,
    build_order_status_reply_prompt,
)
from richpanel_middleware.commerce.order_lookup import lookup_order_summary
from richpanel_middleware.integrations.richpanel.client import (
    RichpanelExecutor,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)
from richpanel_middleware.integrations.richpanel.tickets import (
    TicketMetadata,
    dedupe_tags,
    get_ticket_metadata,
)
from richpanel_middleware.automation.prompts import (
    OrderStatusPromptInput,
    build_order_status_contract,
    prompt_fingerprint,
)
from richpanel_middleware.ingest.envelope import EventEnvelope, normalize_envelope

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow offline tests without boto3."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore

LOGGER = logging.getLogger(__name__)
LOOP_PREVENTION_TAG = "mw-auto-replied"
ORDER_STATUS_REPLY_TAG = "mw-order-status-answered"
ROUTING_APPLIED_TAG = "mw-routing-applied"
EMAIL_SUPPORT_ROUTE_TAG = "route-email-support-team"
ESCALATION_TAG = "mw-escalated-human"
REPLY_SENT_TAG = "mw-reply-sent"
OUTBOUND_PATH_SEND_MESSAGE_TAG = "mw-outbound-path-send-message"
OUTBOUND_PATH_COMMENT_TAG = "mw-outbound-path-comment"
SEND_MESSAGE_FAILED_TAG = "mw-send-message-failed"
SEND_MESSAGE_AUTHOR_MISSING_TAG = "mw-send-message-author-missing"
SEND_MESSAGE_CLOSE_FAILED_TAG = "mw-send-message-close-failed"
SEND_MESSAGE_OPERATOR_MISSING_TAG = "mw-send-message-operator-missing"
OUTBOUND_BLOCKED_ALLOWLIST_TAG = "mw-outbound-blocked-allowlist"
OUTBOUND_BLOCKED_MISSING_BOT_AUTHOR_TAG = "mw-outbound-blocked-missing-bot-author"
MW_OUTBOUND_ALLOWLIST_EMAILS_ENV = "MW_OUTBOUND_ALLOWLIST_EMAILS"
MW_OUTBOUND_ALLOWLIST_DOMAINS_ENV = "MW_OUTBOUND_ALLOWLIST_DOMAINS"
SKIP_RESOLVED_TAG = "mw-skip-order-status-closed"
SKIP_FOLLOWUP_TAG = "mw-skip-followup-after-auto-reply"
SKIP_STATUS_READ_FAILED_TAG = "mw-skip-status-read-failed"
ORDER_LOOKUP_FAILED_TAG = "mw-order-lookup-failed"
ORDER_STATUS_SUPPRESSED_TAG = "mw-order-status-suppressed"
ORDER_LOOKUP_MISSING_PREFIX = "mw-order-lookup-missing"
# Follow-up after auto-reply should route to support without escalation.
_ESCALATION_REASONS: set[str] = {"missing_bot_agent_id", "reply_close_failed"}
_SKIP_REASON_TAGS = {
    "already_resolved": SKIP_RESOLVED_TAG,
    "followup_after_auto_reply": SKIP_FOLLOWUP_TAG,
    "status_read_failed": SKIP_STATUS_READ_FAILED_TAG,
    "send_message_failed": SEND_MESSAGE_FAILED_TAG,
    "send_message_operator_missing": SEND_MESSAGE_OPERATOR_MISSING_TAG,
    "reply_close_failed": SEND_MESSAGE_CLOSE_FAILED_TAG,
    "allowlist_blocked": OUTBOUND_BLOCKED_ALLOWLIST_TAG,
    "missing_bot_agent_id": OUTBOUND_BLOCKED_MISSING_BOT_AUTHOR_TAG,
}
_READ_ONLY_ENVIRONMENTS = {"prod", "production", "staging"}
_SECRET_VALUE_CACHE_TTL_SECONDS = 900
_SECRET_VALUE_CACHE: Dict[str, Dict[str, Any]] = {}


def _is_closed_status(value: Optional[str]) -> bool:
    if value is None:
        return False
    normalized = str(value).strip().lower()
    return normalized in {"resolved", "closed", "solved"}


def _is_valid_order_id(value: Any, *, conversation_id: str) -> bool:
    if value is None:
        return False
    try:
        normalized = str(value).strip()
    except Exception:
        return False
    if not normalized or normalized.lower() == "unknown":
        return False
    if conversation_id and normalized == str(conversation_id):
        return False
    return True


def _normalize_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        normalized = str(value).strip()
    except Exception:
        return None
    return normalized or None


def _normalize_email(value: Any) -> Optional[str]:
    normalized = _normalize_optional_text(value)
    if not normalized:
        return None
    return normalized.lower()


def _normalize_ticket_channel(value: Any) -> Optional[str]:
    normalized = _normalize_optional_text(value)
    if not normalized:
        return None
    return normalized.lower()


def _classify_channel(value: Optional[str]) -> str:
    if not value:
        return "unknown"
    normalized = value.strip().lower()
    if normalized == "email":
        return "email"
    if "chat" in normalized:
        return "chat"
    return "unknown"


def _extract_ticket_channel_from_payload(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    via = payload.get("via")
    if isinstance(via, dict):
        channel = _normalize_ticket_channel(via.get("channel"))
        if channel:
            return channel
    channel = _normalize_ticket_channel(payload.get("channel"))
    if channel:
        return channel
    for nested_key in ("ticket", "data", "conversation"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            channel = _extract_ticket_channel_from_payload(nested)
            if channel:
                return channel
    return None


def _read_only_guard_active(env_name: str) -> bool:
    env_override = os.environ.get("RICHPANEL_READ_ONLY") or os.environ.get(
        "RICH_PANEL_READ_ONLY"
    )
    if env_override is not None:
        return _to_bool(env_override)
    write_disabled = os.environ.get("RICHPANEL_WRITE_DISABLED")
    if write_disabled is not None:
        return _to_bool(write_disabled)
    return env_name in _READ_ONLY_ENVIRONMENTS


def _load_secret_value(secret_id: str) -> Optional[str]:
    now = time.time()
    cached = _SECRET_VALUE_CACHE.get(secret_id)
    if cached and cached.get("expires_at", 0.0) > now:
        return cached.get("value")
    if boto3 is None:
        return None
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_id)
    except (BotoCoreError, ClientError):
        if cached:
            return cached.get("value")
        return None
    secret_value = response.get("SecretString")
    if secret_value is None and response.get("SecretBinary") is not None:
        secret_binary = response.get("SecretBinary")
        if isinstance(secret_binary, (bytes, bytearray)):
            try:
                secret_value = secret_binary.decode("utf-8")
            except (UnicodeDecodeError, ValueError):
                return None
        else:
            try:
                secret_value = base64.b64decode(secret_binary).decode("utf-8")
            except (TypeError, ValueError):
                return None
    if not secret_value:
        return None
    normalized = str(secret_value)
    _SECRET_VALUE_CACHE[secret_id] = {
        "value": normalized,
        "expires_at": now + _SECRET_VALUE_CACHE_TTL_SECONDS,
    }
    return normalized


def _extract_bot_agent_id(secret_value: str) -> Optional[str]:
    try:
        payload = json.loads(secret_value)
    except (TypeError, ValueError):
        return _normalize_optional_text(secret_value)
    if isinstance(payload, (str, int, float)):
        return _normalize_optional_text(payload)
    if isinstance(payload, dict):
        for key in ("bot_agent_id", "agent_id", "id"):
            value = payload.get(key)
            if value is not None:
                return _normalize_optional_text(value)
    return None


def _resolve_bot_agent_id(
    *, env_name: str, allow_network: bool
) -> Tuple[Optional[str], str]:
    env_agent_id = _normalize_optional_text(os.environ.get("RICHPANEL_BOT_AGENT_ID"))
    if env_agent_id:
        return env_agent_id, "env"
    if not allow_network:
        return None, "missing"
    secret_id = f"rp-mw/{env_name}/richpanel/bot_agent_id"
    secret_value = _load_secret_value(secret_id)
    if not secret_value:
        return None, "missing"
    agent_id = _extract_bot_agent_id(secret_value)
    if not agent_id:
        return None, "missing"
    return agent_id, "secrets_manager"


def _parse_allowlist_entries(value: Optional[str], *, strip_at: bool = False) -> set[str]:
    if not value:
        return set()
    entries: set[str] = set()
    for raw in str(value).split(","):
        candidate = raw.strip().lower()
        if not candidate:
            continue
        if strip_at and candidate.startswith("@"):
            candidate = candidate[1:]
        if candidate:
            entries.add(candidate)
    return entries


def _load_outbound_allowlist() -> tuple[set[str], set[str], bool]:
    emails = _parse_allowlist_entries(
        os.environ.get(MW_OUTBOUND_ALLOWLIST_EMAILS_ENV)
    )
    domains = _parse_allowlist_entries(
        os.environ.get(MW_OUTBOUND_ALLOWLIST_DOMAINS_ENV), strip_at=True
    )
    return emails, domains, bool(emails or domains)


def _match_allowlist_email(
    email: Optional[str],
    *,
    allowlist_emails: set[str],
    allowlist_domains: set[str],
) -> tuple[bool, str]:
    if not allowlist_emails and not allowlist_domains:
        return False, "allowlist_empty"
    normalized = _normalize_email(email)
    if not normalized:
        return False, "missing_email"
    if normalized in allowlist_emails:
        return True, "email_match"
    if "@" in normalized:
        domain = normalized.split("@", 1)[1]
        if domain in allowlist_domains:
            return True, "domain_match"
    return False, "not_allowlisted"


def _extract_customer_email_from_payload(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    candidates: List[Any] = []
    for key in ("email", "customer_email", "customerEmail", "from_email", "fromEmail"):
        candidates.append(payload.get(key))
    for key in ("customer_profile", "customer", "requester", "sender", "user"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            candidates.append(nested.get("email"))
            candidates.append(nested.get("address"))
    via = payload.get("via")
    if isinstance(via, dict):
        source = via.get("source")
        if isinstance(source, dict):
            from_obj = source.get("from")
            if isinstance(from_obj, dict):
                candidates.append(from_obj.get("address") or from_obj.get("email"))
            elif isinstance(from_obj, str):
                candidates.append(from_obj)
        from_obj = via.get("from")
        if isinstance(from_obj, dict):
            candidates.append(from_obj.get("address") or from_obj.get("email"))
        elif isinstance(from_obj, str):
            candidates.append(from_obj)
    for candidate in candidates:
        normalized = _normalize_email(candidate)
        if normalized:
            return normalized
    return None


def _tracking_signal_present(order_summary: Dict[str, Any]) -> bool:
    if not isinstance(order_summary, dict):
        return False
    for key in ("tracking_number", "tracking", "tracking_no", "trackingCode"):
        if order_summary.get(key):
            return True
    for key in ("tracking_url", "trackingUrl", "tracking_link", "status_url"):
        if order_summary.get(key):
            return True
    for key in ("carrier", "shipping_carrier", "carrier_name", "carrierName"):
        if order_summary.get(key):
            return True
    return False


def _missing_order_context(
    order_summary: Optional[Dict[str, Any]],
    envelope: EventEnvelope,
    payload: Dict[str, Any],
) -> List[str]:
    summary = order_summary or {}
    missing: List[str] = []

    order_id = (
        summary.get("order_id")
        or summary.get("id")
        or payload.get("order_id")
        or payload.get("orderId")
        or payload.get("order_number")
        or payload.get("orderNumber")
        or payload.get("id")
    )
    if not _is_valid_order_id(order_id, conversation_id=envelope.conversation_id):
        missing.append("order_id")

    created_at = (
        summary.get("created_at")
        or summary.get("order_created_at")
        or payload.get("created_at")
        or payload.get("order_created_at")
        or payload.get("ordered_at")
        or payload.get("order_date")
    )
    if not created_at:
        missing.append("created_at")

    tracking_present = _tracking_signal_present(summary)
    shipping_method = (
        summary.get("shipping_method")
        or summary.get("shipping_method_name")
        or payload.get("shipping_method")
        or payload.get("shipping_method_name")
        or payload.get("shipping_service")
        or payload.get("shipping_option")
    )
    shipping_bucket = normalize_shipping_method(shipping_method) is not None
    if not tracking_present and not shipping_bucket:
        missing.append(
            "tracking_or_shipping_method"
            if not shipping_method
            else "shipping_method_bucket"
        )

    return missing


def _missing_context_reason_tag(missing_fields: List[str]) -> Optional[str]:
    for missing_field in missing_fields:
        if missing_field == "order_id":
            return f"{ORDER_LOOKUP_MISSING_PREFIX}:order_id"
        if missing_field == "created_at":
            return f"{ORDER_LOOKUP_MISSING_PREFIX}:created_at"
        if missing_field == "tracking_or_shipping_method":
            return f"{ORDER_LOOKUP_MISSING_PREFIX}:tracking_or_shipping_method"
        if missing_field == "shipping_method_bucket":
            return f"{ORDER_LOOKUP_MISSING_PREFIX}:shipping_method_bucket"
    return None


def _order_status_intent_rejection_reason(intent: OrderStatusIntentArtifact) -> str:
    if intent.gated_reason:
        return f"order_status_intent_gated:{intent.gated_reason}"
    if intent.parse_error:
        return f"order_status_intent_parse_failed:{intent.parse_error}"
    if intent.result and not intent.result.is_order_status:
        return "order_status_intent_not_order_status"
    if intent.result and intent.result.confidence < intent.confidence_threshold:
        return "order_status_intent_low_confidence"
    return "order_status_intent_rejected"


@dataclass
class ActionPlan:
    """Structured representation of what the worker intends to do."""

    event_id: str
    mode: str
    safe_mode: bool
    automation_enabled: bool
    actions: List[Dict[str, Any]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    routing: RoutingDecision | None = None
    routing_artifact: RoutingArtifact | None = None
    order_status_intent: OrderStatusIntentArtifact | None = None


@dataclass
class ExecutionResult:
    """Outcome of the execute step (dry-run by default)."""

    event_id: str
    mode: str
    dry_run: bool
    actions: List[Dict[str, Any]]
    routing: RoutingDecision
    state_record: Dict[str, Any]
    audit_record: Dict[str, Any]


def normalize_event(raw_event: Dict[str, Any]) -> EventEnvelope:
    """Normalize raw event payload into the canonical envelope."""
    return normalize_envelope(raw_event)


def _fingerprint(obj: Any, *, length: int = 12) -> str:
    try:
        serialized = json.dumps(obj, sort_keys=True, default=str)
    except Exception:
        serialized = str(obj)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]


def _hash_identifier(value: Optional[str], *, length: int = 8) -> Optional[str]:
    if not value:
        return None
    try:
        normalized = str(value).strip()
    except Exception:
        return None
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:length]


def _redact_actions_for_storage(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Strip reply bodies and payloads from actions before persisting to Dynamo.
    """
    sanitized: List[Dict[str, Any]] = []
    for action in actions or []:
        safe_action: Dict[str, Any] = {
            "type": action.get("type"),
            "note": action.get("note"),
            "enabled": action.get("enabled"),
            "dry_run": action.get("dry_run"),
            "reasons": action.get("reasons"),
        }
        params = action.get("parameters") or {}
        redacted_params: Dict[str, Any] = {}
        if "prompt_fingerprint" in params:
            redacted_params["prompt_fingerprint"] = params.get("prompt_fingerprint")
        if "order_summary" in params:
            redacted_params["order_summary_fingerprint"] = _fingerprint(
                params.get("order_summary")
            )
        if "draft_reply" in params:
            redacted_params["draft_reply_fingerprint"] = _fingerprint(
                params.get("draft_reply")
            )
            redacted_params["has_draft_reply"] = bool(params.get("draft_reply"))
        if "delivery_estimate" in params:
            redacted_params["delivery_estimate_present"] = bool(
                params.get("delivery_estimate")
            )
        if redacted_params:
            safe_action["parameters"] = redacted_params
        sanitized.append({k: v for k, v in safe_action.items() if v is not None})
    return sanitized


def _safe_ticket_metadata_fetch(
    ticket_id: str,
    *,
    executor: RichpanelExecutor,
    allow_network: bool,
) -> Optional[TicketMetadata]:
    """
    Fetch ticket status + tags without logging the ticket body.
    """
    try:
        return get_ticket_metadata(ticket_id, executor, allow_network=allow_network)
    except (RichpanelRequestError, SecretLoadError, TransportError):
        return None


def _safe_ticket_snapshot_fetch(
    ticket_id: str,
    *,
    executor: RichpanelExecutor,
    allow_network: bool,
) -> Tuple[Optional[TicketMetadata], Optional[str], Optional[str]]:
    """
    Fetch PII-safe ticket metadata plus channel (via.channel) and customer email.
    """
    try:
        encoded_id = urllib.parse.quote(str(ticket_id), safe="")
        response = executor.execute(
            "GET",
            f"/v1/tickets/{encoded_id}",
            dry_run=not allow_network,
            log_body_excerpt=False,
        )
    except (RichpanelRequestError, SecretLoadError, TransportError):
        return None, None, None

    if response.dry_run:
        return (
            TicketMetadata(
                status=None, tags=set(), status_code=response.status_code, dry_run=True
            ),
            None,
            None,
        )

    if response.status_code < 200 or response.status_code >= 300:
        return None, None, None

    payload = response.json() or {}
    if not isinstance(payload, dict):
        payload = {}

    ticket_obj = payload.get("ticket")
    ticket_payload = ticket_obj if isinstance(ticket_obj, dict) else payload

    status = _normalize_optional_text(
        ticket_payload.get("status") or ticket_payload.get("state")
    )
    tags = dedupe_tags(ticket_payload.get("tags"))

    channel = _extract_ticket_channel_from_payload(ticket_payload)

    customer_email = _extract_customer_email_from_payload(ticket_payload)

    return (
        TicketMetadata(
            status=status,
            tags=tags,
            status_code=response.status_code,
            dry_run=response.dry_run,
        ),
        channel,
        customer_email,
    )


def _comment_operator_flag(comment: Any) -> Optional[bool]:
    if not isinstance(comment, dict):
        return None
    value = comment.get("is_operator")
    if value is None:
        value = comment.get("isOperator")
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
    return None


def _comment_created_at(comment: Any) -> Optional[datetime]:
    if not isinstance(comment, dict):
        return None
    raw = comment.get("created_at") or comment.get("createdAt")
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _latest_comment_entry(comments: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(comments, list) or not comments:
        return None
    latest_comment = None
    latest_timestamp = None
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        timestamp = _comment_created_at(comment)
        if timestamp is None:
            continue
        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_comment = comment
    if latest_comment is not None:
        return latest_comment
    for comment in reversed(comments):
        if isinstance(comment, dict):
            return comment
    return None


def _latest_comment_is_operator(comments: Any) -> Optional[bool]:
    latest_comment = _latest_comment_entry(comments)
    if latest_comment is None:
        return None
    return _comment_operator_flag(latest_comment)


def _safe_ticket_comment_operator_fetch(
    ticket_id: str,
    *,
    executor: RichpanelExecutor,
    allow_network: bool,
) -> Optional[bool]:
    try:
        encoded_id = urllib.parse.quote(str(ticket_id), safe="")
        response = executor.execute(
            "GET",
            f"/v1/tickets/{encoded_id}",
            dry_run=not allow_network,
            log_body_excerpt=False,
        )
    except (RichpanelRequestError, SecretLoadError, TransportError):
        return None
    if response.dry_run:
        return None
    if response.status_code < 200 or response.status_code >= 300:
        return None
    payload = response.json() or {}
    if not isinstance(payload, dict):
        return None
    ticket_obj = payload.get("ticket")
    ticket_payload = ticket_obj if isinstance(ticket_obj, dict) else payload
    comments = ticket_payload.get("comments") if isinstance(ticket_payload, dict) else None
    return _latest_comment_is_operator(comments)


def _resolve_target_ticket_id(
    envelope: EventEnvelope,
    *,
    executor: RichpanelExecutor,
    allow_network: bool,
) -> str:
    """
    Resolve the canonical Richpanel ticket id, preferring ticket_number when present.
    Falls back to envelope.conversation_id.
    """
    payload = envelope.payload if isinstance(envelope.payload, dict) else {}
    ticket_number = payload.get("ticket_number") or payload.get("conversation_no")
    if ticket_number:
        encoded_number = urllib.parse.quote(str(ticket_number), safe="")
        try:
            resp = executor.execute(
                "GET",
                f"/v1/tickets/number/{encoded_number}",
                dry_run=not allow_network,
                log_body_excerpt=False,
            )
            if resp.status_code == 200:
                body = resp.json() or {}
                ticket_obj = body.get("ticket") if isinstance(body, dict) else {}
                if isinstance(ticket_obj, dict) and ticket_obj.get("id"):
                    return str(ticket_obj.get("id"))
        except (RichpanelRequestError, SecretLoadError, TransportError):
            pass
    return str(envelope.conversation_id)


def plan_actions(
    envelope: EventEnvelope,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool = False,
    outbound_enabled: bool = False,
) -> ActionPlan:
    """
    Build a minimal action plan from the normalized envelope.

    In v1 the plan is intentionally conservative and dry-run only.

    Advisory LLM routing:
    - Always computes deterministic routing as baseline
    - Computes LLM routing suggestion (dry-run artifact if gated)
    - Persists both into routing_artifact for audit/analysis
    - Uses OPENAI_ROUTING_PRIMARY flag to determine final routing source
    """
    payload = envelope.payload if isinstance(envelope.payload, dict) else {}

    # Compute dual routing (deterministic + LLM advisory)
    force_openai_primary = bool(
        payload.get("force_openai_routing_primary")
        if isinstance(payload, dict) and payload.get("source") == "dev_e2e_smoke"
        else False
    )
    routing, routing_artifact = compute_dual_routing(
        payload,
        conversation_id=envelope.conversation_id,
        event_id=envelope.event_id,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
        force_primary=force_openai_primary,
    )

    customer_message = extract_customer_message(payload, default="")
    intent_metadata: Dict[str, str] = {}
    ticket_channel = _extract_ticket_channel_from_payload(payload)
    if ticket_channel:
        intent_metadata["ticket_channel"] = ticket_channel
    order_status_intent = classify_order_status_intent(
        customer_message,
        conversation_id=envelope.conversation_id,
        event_id=envelope.event_id,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
        metadata=intent_metadata or None,
    )

    effective_automation = automation_enabled and not safe_mode
    mode = "automation_candidate" if effective_automation else "route_only"

    reasons: List[str] = []
    if safe_mode:
        reasons.append("safe_mode")
    if not automation_enabled:
        reasons.append("automation_disabled")
    reasons.append(routing.reason)

    actions: List[Dict[str, Any]] = []
    routing_payload = asdict(routing) if routing else None
    if mode == "route_only":
        actions.append(
            {
                "type": "route_only",
                "conversation_id": envelope.conversation_id,
                "note": "automation disabled; dry-run logging only",
                "reasons": reasons,
                "routing": routing_payload,
            }
        )
    else:
        actions.append(
            {
                "type": "analyze",
                "conversation_id": envelope.conversation_id,
                "note": "automation candidate (dry-run)",
                "reasons": reasons,
                "routing": routing_payload,
            }
        )

        if routing.intent in {"order_status_tracking", "shipping_delay_not_shipped"}:
            if not order_status_intent.accepted:
                reasons.append(_order_status_intent_rejection_reason(order_status_intent))
                if routing:
                    extra_tags = [
                        EMAIL_SUPPORT_ROUTE_TAG,
                        ORDER_STATUS_SUPPRESSED_TAG,
                    ]
                    routing.tags = sorted(dedupe_tags((routing.tags or []) + extra_tags))
                    if actions:
                        actions[0]["routing"] = asdict(routing)
                return ActionPlan(
                    event_id=envelope.event_id,
                    mode=mode,
                    safe_mode=safe_mode,
                    automation_enabled=automation_enabled,
                    actions=actions,
                    reasons=reasons,
                    routing=routing,
                    routing_artifact=routing_artifact,
                    order_status_intent=order_status_intent,
                )
            order_summary = lookup_order_summary(
                envelope,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
            )
            missing_fields = _missing_order_context(order_summary, envelope, payload)
            if missing_fields:
                reasons.append("order_context_missing")
                reason_tag = _missing_context_reason_tag(missing_fields)
                if routing:
                    extra_tags = [
                        EMAIL_SUPPORT_ROUTE_TAG,
                        ORDER_LOOKUP_FAILED_TAG,
                        ORDER_STATUS_SUPPRESSED_TAG,
                    ]
                    if reason_tag:
                        extra_tags.append(reason_tag)
                    routing.tags = sorted(
                        dedupe_tags((routing.tags or []) + extra_tags)
                    )
                    if actions:
                        actions[0]["routing"] = asdict(routing)
                ticket_number = payload.get("ticket_number") or payload.get(
                    "conversation_no"
                )
                LOGGER.info(
                    "automation.order_status_context_missing",
                    extra={
                        "event_id": envelope.event_id,
                        "conversation_id": envelope.conversation_id,
                        "ticket_id": envelope.conversation_id,
                        "ticket_number": ticket_number,
                        "order_lookup_result": "missing_context",
                        "missing_fields": missing_fields,
                    },
                )
                return ActionPlan(
                    event_id=envelope.event_id,
                    mode=mode,
                    safe_mode=safe_mode,
                    automation_enabled=automation_enabled,
                    actions=actions,
                    reasons=reasons,
                    routing=routing,
                    routing_artifact=routing_artifact,
                    order_status_intent=order_status_intent,
                )
            ticket_created_at = (
                payload.get("ticket_created_at")
                or payload.get("created_at")
                or envelope.received_at
            )
            delivery_estimate = None
            draft_reply = build_tracking_reply(order_summary)
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
                if delivery_estimate:
                    order_summary["delivery_estimate"] = delivery_estimate
                draft_reply = build_no_tracking_reply(
                    order_summary,
                    inquiry_date=ticket_created_at,
                    delivery_estimate=delivery_estimate,
                )
            prompt_input = OrderStatusPromptInput(
                name="order_status_draft_reply",
                conversation_id=envelope.conversation_id,
                customer_message=extract_customer_message(
                    payload, default="Order status request"
                ),
                order_summary=order_summary,
                customer_profile=payload.get("customer_profile"),
            )
            contract = build_order_status_contract(prompt_input)
            parameters: Dict[str, Any] = {
                "order_summary": order_summary,
                "prompt_fingerprint": prompt_fingerprint(contract),
            }
            if delivery_estimate:
                parameters["delivery_estimate"] = delivery_estimate
            if draft_reply:
                parameters["draft_reply"] = draft_reply

            actions.append(
                {
                    "type": "order_status_draft_reply",
                    "conversation_id": envelope.conversation_id,
                    "note": "order status draft reply (dry-run)",
                    "enabled": False,
                    "dry_run": True,
                    "parameters": parameters,
                    "reasons": reasons,
                }
            )

    return ActionPlan(
        event_id=envelope.event_id,
        mode=mode,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        actions=actions,
        reasons=reasons,
        routing=routing,
        routing_artifact=routing_artifact,
        order_status_intent=order_status_intent,
    )


def execute_plan(
    envelope: EventEnvelope,
    plan: ActionPlan,
    *,
    dry_run: bool = True,
    state_writer: Optional[Callable[[Dict[str, Any]], None]] = None,
    audit_writer: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> ExecutionResult:
    """
    Execute the plan in dry-run mode: record intent and emit audit/state records.

    External side effects are intentionally stubbed; writers allow the caller to
    persist state (e.g., DynamoDB) when desired.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    actions_for_storage = _redact_actions_for_storage(plan.actions)

    state_record: Dict[str, Any] = {
        "conversation_id": envelope.conversation_id,
        "event_id": envelope.event_id,
        "mode": plan.mode,
        "actions": actions_for_storage,
        "action_count": len(actions_for_storage),
        "safe_mode": plan.safe_mode,
        "automation_enabled": plan.automation_enabled,
        "dry_run": dry_run,
        "updated_at": timestamp,
    }
    audit_record: Dict[str, Any] = {
        "event_id": envelope.event_id,
        "conversation_id": envelope.conversation_id,
        "recorded_at": timestamp,
        "mode": plan.mode,
        "actions": actions_for_storage,
        "reasons": plan.reasons,
        "dry_run": dry_run,
        "source": envelope.source,
    }
    if plan.routing:
        routing_dict = asdict(plan.routing)
        state_record["routing"] = routing_dict
        audit_record["routing"] = routing_dict

    # Persist routing artifact for dual routing analysis
    if plan.routing_artifact:
        routing_artifact_dict = plan.routing_artifact.to_dict()
        state_record["routing_artifact"] = routing_artifact_dict
        audit_record["routing_artifact"] = routing_artifact_dict
        # Add primary_source to top level for easy querying
        state_record["routing_primary_source"] = plan.routing_artifact.primary_source
        audit_record["routing_primary_source"] = plan.routing_artifact.primary_source

    if plan.order_status_intent:
        intent_dict = plan.order_status_intent.to_dict()
        state_record["order_status_intent"] = intent_dict
        audit_record["order_status_intent"] = intent_dict

    if state_writer:
        state_writer(state_record)
    if audit_writer:
        audit_writer(audit_record)

    return ExecutionResult(
        event_id=envelope.event_id,
        mode=plan.mode,
        dry_run=dry_run,
        actions=actions_for_storage,
        routing=(
            plan.routing
            if plan.routing
            else RoutingDecision(
                category="general",
                tags=[],
                reason="routing missing",
                department="Email Support Team",
                intent="unknown",
            )
        ),
        state_record=state_record,
        audit_record=audit_record,
    )


def _find_order_status_action(plan: ActionPlan) -> Optional[Dict[str, Any]]:
    for action in plan.actions:
        if action.get("type") == "order_status_draft_reply":
            return action
    return None


_REWRITE_REASON_ERROR_CLASS = {
    "request_failed": "OpenAIRequestError",
    "invalid_json": "OpenAIResponseParseError",
    "not_a_dict": "OpenAIResponseParseError",
    "missing_body": "OpenAIResponseParseError",
    "low_confidence": "OpenAILowConfidence",
    "risk_flagged": "OpenAIRiskFlagged",
    "dry_run": "OpenAIDryRun",
    "missing_required_tokens": "OpenAIInvariantViolation",
    "missing_required_urls": "OpenAIInvariantViolation",
    "missing_required_tracking": "OpenAIInvariantViolation",
    "missing_required_eta": "OpenAIInvariantViolation",
    "unexpected_tokens": "OpenAIInvariantViolation",
    "unexpected_urls": "OpenAIInvariantViolation",
    "unexpected_tracking": "OpenAIInvariantViolation",
    "unexpected_eta": "OpenAIInvariantViolation",
    "contains_internal_tags": "OpenAIInvariantViolation",
}


def _rewrite_error_class(
    reason: Optional[str], error_class: Optional[str]
) -> Optional[str]:
    if error_class:
        return error_class
    if not reason:
        return None
    return _REWRITE_REASON_ERROR_CLASS.get(reason)


def _fingerprint_reply_body(body: Optional[str]) -> Optional[str]:
    if not body:
        return None
    try:
        serialized = json.dumps(body, ensure_ascii=False, sort_keys=True)
    except Exception:
        serialized = str(body)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:12]


def _build_openai_rewrite_evidence(
    rewrite_result: Optional[ReplyRewriteResult],
    *,
    reason: Optional[str] = None,
    error_class: Optional[str] = None,
) -> Dict[str, Any]:
    if rewrite_result:
        rewrite_attempted = bool(rewrite_result.llm_called)
        rewrite_applied = bool(rewrite_result.rewritten)
        fallback_used = rewrite_attempted and not rewrite_applied
        rewrite_reason = reason or rewrite_result.reason
        final_error_class = (
            _rewrite_error_class(rewrite_reason, rewrite_result.error_class)
            if fallback_used
            else None
        )
        return {
            "rewrite_attempted": rewrite_attempted,
            "rewrite_applied": rewrite_applied,
            "model": rewrite_result.model,
            "response_id": rewrite_result.response_id,
            "response_id_unavailable_reason": rewrite_result.response_id_unavailable_reason,
            "fallback_used": fallback_used,
            "reason": rewrite_reason,
            "error_class": final_error_class,
        }
    return {
        "rewrite_attempted": False,
        "rewrite_applied": False,
        "model": None,
        "response_id": None,
        "response_id_unavailable_reason": reason or "not_attempted",
        "fallback_used": False,
        "reason": reason or "not_attempted",
        "error_class": _rewrite_error_class(reason, error_class),
    }


def _outbound_block_reason(
    *,
    outbound_enabled: bool,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    has_action: bool,
    read_only_guard_active: bool,
) -> Optional[str]:
    if not outbound_enabled:
        return "outbound_disabled"
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
    if read_only_guard_active:
        return "read_only_guard"
    if not allow_network:
        return "network_disabled"
    if not has_action:
        return "missing_order_status_action"
    return None


def execute_order_status_reply(
    envelope: EventEnvelope,
    plan: ActionPlan,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
    richpanel_executor: Optional[RichpanelExecutor] = None,
    loop_prevention_tag: str = LOOP_PREVENTION_TAG,
) -> Dict[str, Any]:
    """
    Post the order-status draft reply to Richpanel and resolve the ticket when enabled.

    The call is heavily gated to stay fail-closed:
    - defaults to outbound disabled (env RICHPANEL_OUTBOUND_ENABLED)
    - requires safe_mode == False, automation_enabled == True, allow_network == True
    - requires a draft reply payload on the action plan
    """
    order_action = _find_order_status_action(plan)
    payload = envelope.payload if isinstance(envelope.payload, dict) else {}
    env_name, _ = resolve_env_name()
    is_prod_env = env_name in PRODUCTION_ENVIRONMENTS
    read_only_guard_active = _read_only_guard_active(env_name)
    payload_channel = _extract_ticket_channel_from_payload(payload)
    channel_detected = _classify_channel(payload_channel)
    channel_detection_source = "webhook" if payload_channel else "unknown"
    bot_agent_id_source = "missing"
    def _metadata() -> Dict[str, Any]:
        return {
            "channel_detected": channel_detected,
            "channel_detection_source": channel_detection_source,
            "bot_agent_id_source": bot_agent_id_source,
            "read_only_guard_active": read_only_guard_active,
        }
    reason = _outbound_block_reason(
        outbound_enabled=outbound_enabled,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        has_action=order_action is not None,
        read_only_guard_active=read_only_guard_active,
    )
    if reason and reason != "missing_order_status_action":
        dry_run_would_send_message = bool(
            channel_detected == "email"
            and order_action is not None
            and reason in {"outbound_disabled", "read_only_guard"}
        )
        LOGGER.info(
            "automation.order_status_reply.skip",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
                "reason": reason,
                "outbound_enabled": outbound_enabled,
                "allow_network": allow_network,
                "channel_detected": channel_detected,
                "channel_detection_source": channel_detection_source,
                "bot_agent_id_source": bot_agent_id_source,
                "read_only_guard_active": read_only_guard_active,
                "dry_run_would_send_message": dry_run_would_send_message,
            },
        )
        return {
            "sent": False,
            "reason": reason,
            "dry_run_would_send_message": dry_run_would_send_message,
            **_metadata(),
        }

    executor = richpanel_executor or RichpanelExecutor(
        outbound_enabled=outbound_enabled
        and allow_network
        and automation_enabled
        and not safe_mode
    )

    responses: List[Dict[str, Any]] = []
    openai_rewrite = None
    try:
        # URL-encode conversation_id for write operations (email IDs have special chars)
        target_id = _resolve_target_ticket_id(
            envelope, executor=executor, allow_network=allow_network
        )
        encoded_id = urllib.parse.quote(str(target_id), safe="")
        run_id = None
        if isinstance(envelope.payload, dict):
            run_id = envelope.payload.get("run_id") or envelope.payload.get("RUN_ID")
        run_specific_reply_tag = (
            f"{ORDER_STATUS_REPLY_TAG}:{run_id}" if run_id else ORDER_STATUS_REPLY_TAG
        )

        ticket_metadata, ticket_channel, ticket_customer_email = _safe_ticket_snapshot_fetch(
            target_id,
            executor=executor,
            allow_network=allow_network,
        )
        resolved_channel = payload_channel or ticket_channel
        channel_detected = _classify_channel(resolved_channel)
        if payload_channel:
            channel_detection_source = "webhook"
        elif ticket_channel:
            channel_detection_source = "fetched_ticket"
        else:
            channel_detection_source = "unknown"

        def _route_email_support(
            reason: str,
            ticket_status: Optional[str] = None,
            *,
            extra_tags: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            route_tags = [EMAIL_SUPPORT_ROUTE_TAG]
            skip_tag = _SKIP_REASON_TAGS.get(reason)
            if skip_tag:
                route_tags.append(skip_tag)
            if extra_tags:
                route_tags.extend(extra_tags)
            if reason in _ESCALATION_REASONS:
                route_tags.append(ESCALATION_TAG)
            route_tags = sorted(dedupe_tags(route_tags))

            route_response = executor.execute(
                "PUT",
                f"/v1/tickets/{encoded_id}/add-tags",
                json_body={"tags": route_tags},
                dry_run=not allow_network,
            )
            responses.append(
                {
                    "action": "route_email_support",
                    "status": route_response.status_code,
                    "dry_run": route_response.dry_run,
                    "tags": route_tags,
                }
            )
            LOGGER.info(
                "automation.order_status_reply.skip",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                    "reason": reason,
                    "ticket_status": ticket_status,
                    "route_tags": route_tags,
                },
            )
            return {
                "sent": False,
                "reason": reason,
                "ticket_status": ticket_status,
                "responses": responses,
            }

        if ticket_metadata is None:
            result = _route_email_support("status_read_failed")
            result.update(_metadata())
            return result

        ticket_status = ticket_metadata.status
        is_email_channel = channel_detected == "email"

        if loop_prevention_tag in (ticket_metadata.tags or set()):
            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
            # no escalation). Preserve loop-prevention tag to avoid repeated replies,
            # even if the ticket is already closed.
            result = _route_email_support(
                "followup_after_auto_reply", ticket_status=ticket_status
            )
            result.update(_metadata())
            return result

        if order_action is None:
            LOGGER.info(
                "automation.order_status_reply.skip",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                    "reason": "missing_order_status_action",
                },
            )
            return {"sent": False, "reason": "missing_order_status_action", **_metadata()}

        if _is_closed_status(ticket_status):
            result = _route_email_support("already_resolved", ticket_status=ticket_status)
            result.update(_metadata())
            return result

        (
            allowlist_emails,
            allowlist_domains,
            allowlist_configured,
        ) = _load_outbound_allowlist()
        allowlist_required = is_prod_env or allowlist_configured
        if allowlist_required:
            customer_email = ticket_customer_email or _extract_customer_email_from_payload(
                payload
            )
            allowlist_allowed, allowlist_reason = _match_allowlist_email(
                customer_email,
                allowlist_emails=allowlist_emails,
                allowlist_domains=allowlist_domains,
            )
            if not allowlist_allowed:
                LOGGER.info(
                    "automation.order_status_reply.allowlist_blocked",
                    extra={
                        "event_id": envelope.event_id,
                        "conversation_id": envelope.conversation_id,
                        "environment": env_name,
                        "allowlist_required": allowlist_required,
                        "allowlist_configured": allowlist_configured,
                        "allowlist_reason": allowlist_reason,
                        "ticket_channel": resolved_channel,
                        "customer_email_hash": _hash_identifier(customer_email),
                    },
                )
                result = _route_email_support(
                    "allowlist_blocked", ticket_status=ticket_status
                )
                result.update(_metadata())
                return result

        parameters = order_action.get("parameters") or {}
        draft_reply = parameters.get("draft_reply") or {}
        reply_body = draft_reply.get("body")
        if not reply_body:
            LOGGER.info(
                "automation.order_status_reply.skip",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                    "reason": "missing_draft_reply",
                },
            )
            return {"sent": False, "reason": "missing_draft_reply", **_metadata()}

        order_summary = parameters.get("order_summary") or {}
        delivery_estimate = parameters.get("delivery_estimate") or order_summary.get(
            "delivery_estimate"
        )
        if not isinstance(delivery_estimate, dict):
            delivery_estimate = {}
        eta_window = delivery_estimate.get("eta_human") or draft_reply.get("eta_human")
        shipping_method = (
            delivery_estimate.get("normalized_method")
            or order_summary.get("shipping_method_name")
            or order_summary.get("shipping_method")
        )
        reply_context = OrderStatusReplyContext(
            tracking_number=draft_reply.get("tracking_number"),
            tracking_url=draft_reply.get("tracking_url"),
            eta_window=eta_window,
            shipping_method=shipping_method,
            carrier=draft_reply.get("carrier"),
        )
        intent_language = None
        if isinstance(plan.order_status_intent, OrderStatusIntentArtifact):
            intent_result = plan.order_status_intent.result
            if intent_result and intent_result.language:
                intent_language = intent_result.language
        prompt_messages = build_order_status_reply_prompt(
            context=reply_context,
            draft_reply=reply_body,
            language=intent_language,
        )

        original_hash = _fingerprint_reply_body(reply_body)
        rewrite_result: ReplyRewriteResult | None = None
        openai_rewrite = {}
        try:
            rewrite_result = rewrite_reply(
                reply_body,
                conversation_id=envelope.conversation_id,
                event_id=envelope.event_id,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
                outbound_enabled=outbound_enabled,
                prompt_messages=prompt_messages,
            )
            if rewrite_result.rewritten and rewrite_result.body:
                reply_body = rewrite_result.body
            openai_rewrite = _build_openai_rewrite_evidence(rewrite_result)
        except Exception as exc:
            error_class = exc.__class__.__name__
            openai_rewrite = {
                "rewrite_attempted": True,
                "rewrite_applied": False,
                "model": None,
                "response_id": None,
                "response_id_unavailable_reason": "exception",
                "fallback_used": True,
                "reason": "exception",
                "error_class": error_class,
            }
            LOGGER.exception(
                "automation.order_status_reply.rewrite_failed",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                },
            )

        rewritten_hash = _fingerprint_reply_body(reply_body)
        rewritten_changed = None
        if original_hash and rewritten_hash:
            rewritten_changed = original_hash != rewritten_hash
        openai_rewrite["original_hash"] = original_hash
        openai_rewrite["rewritten_hash"] = rewritten_hash
        openai_rewrite["rewritten_changed"] = rewritten_changed

        if rewrite_result:
            responses.append(
                {
                    "action": "reply_rewrite",
                    "rewritten": rewrite_result.rewritten,
                    "reason": rewrite_result.reason,
                    "confidence": rewrite_result.confidence,
                    "dry_run": rewrite_result.dry_run,
                    "model": rewrite_result.model,
                    "risk_flags": rewrite_result.risk_flags,
                    "fingerprint": rewrite_result.fingerprint,
                    "llm_called": rewrite_result.llm_called,
                    "response_id": rewrite_result.response_id,
                    "response_id_unavailable_reason": rewrite_result.response_id_unavailable_reason,
                    "error_class": rewrite_result.error_class,
                }
            )

        comment_payload = {"body": reply_body, "type": "public", "source": "middleware"}
        # Try minimal working payloads first (state-only), then add status/comment variants.
        update_candidates: List[Tuple[str, Dict[str, Any]]] = [
            ("ticket_state_closed", {"ticket": {"state": "closed", "comment": comment_payload}}),
            ("ticket_status_closed", {"ticket": {"status": "closed", "comment": comment_payload}}),
            ("ticket_state_resolved", {"ticket": {"state": "resolved", "comment": comment_payload}}),
            ("ticket_status_resolved", {"ticket": {"status": "resolved", "comment": comment_payload}}),
            ("state_closed", {"state": "closed", "comment": comment_payload}),
            ("status_closed", {"status": "closed", "comment": comment_payload}),
            ("state_resolved", {"state": "resolved", "comment": comment_payload}),
            ("status_resolved", {"status": "resolved", "comment": comment_payload}),
            ("ticket_state_closed_status_CLOSED", {"ticket": {"state": "closed", "status": "CLOSED", "comment": comment_payload}}),
            ("ticket_state_CLOSED_status_CLOSED", {"ticket": {"state": "CLOSED", "status": "CLOSED", "comment": comment_payload}}),
            ("ticket_state_CLOSED", {"ticket": {"state": "CLOSED", "comment": comment_payload}}),
            ("ticket_state_RESOLVED", {"ticket": {"state": "RESOLVED", "comment": comment_payload}}),
            ("ticket_state_resolved_status_RESOLVED", {"ticket": {"state": "resolved", "status": "RESOLVED", "comment": comment_payload}}),
            ("ticket_status_resolved_state_RESOLVED", {"ticket": {"status": "resolved", "state": "RESOLVED", "comment": comment_payload}}),
            ("state_CLOSED", {"state": "CLOSED", "comment": comment_payload}),
            ("status_CLOSED", {"status": "CLOSED", "comment": comment_payload}),
            ("state_RESOLVED", {"state": "RESOLVED", "comment": comment_payload}),
            ("status_RESOLVED", {"status": "RESOLVED", "comment": comment_payload}),
        ]

        def _strip_comment(payload: Any) -> Dict[str, Any]:
            if not isinstance(payload, dict):
                return {}
            sanitized = dict(payload)
            if "comment" in sanitized:
                sanitized.pop("comment", None)
            ticket_payload = sanitized.get("ticket")
            if isinstance(ticket_payload, dict):
                ticket_payload = dict(ticket_payload)
                ticket_payload.pop("comment", None)
                sanitized["ticket"] = ticket_payload
            return sanitized

        def _payload_has_comment(payload: Any) -> bool:
            if not isinstance(payload, dict):
                return False
            if payload.get("comment"):
                return True
            ticket_payload = payload.get("ticket")
            return isinstance(ticket_payload, dict) and bool(ticket_payload.get("comment"))

        close_candidates = [
            (candidate_name, _strip_comment(payload))
            for candidate_name, payload in update_candidates
        ]

        def _apply_update_candidates(
            candidates: List[Tuple[str, Dict[str, Any]]],
            *,
            strip_comment_after_success: bool,
        ) -> Optional[str]:
            update_success = None
            comment_sent = False
            for candidate_name, payload in candidates:
                payload_dict = cast(Dict[str, Any], payload)
                payload_to_send: Dict[str, Any] = payload_dict
                if strip_comment_after_success and comment_sent:
                    payload_to_send = _strip_comment(payload_dict)
                reply_response = executor.execute(
                    "PUT",
                    f"/v1/tickets/{encoded_id}",
                    json_body=payload_to_send,
                    dry_run=not allow_network,
                )
                candidate_success = (
                    200 <= reply_response.status_code < 300
                    and not reply_response.dry_run
                )
                if (
                    candidate_success
                    and strip_comment_after_success
                    and _payload_has_comment(payload_to_send)
                ):
                    comment_sent = True
                closed_after = None
                if candidate_success:
                    refreshed = _safe_ticket_metadata_fetch(
                        target_id,
                        executor=executor,
                        allow_network=allow_network,
                    )
                    closed_after = (
                        _is_closed_status(refreshed.status) if refreshed else None
                    )
                    if closed_after is not True:
                        candidate_success = False
                responses.append(
                    {
                        "action": "reply_and_resolve",
                        "status": reply_response.status_code,
                        "dry_run": reply_response.dry_run,
                        "candidate": candidate_name,
                        "update_success": candidate_success,
                        "closed_after": closed_after,
                    }
                )
                LOGGER.info(
                    "automation.order_status_reply.update_candidate",
                    extra={
                        "event_id": envelope.event_id,
                        "conversation_id": envelope.conversation_id,
                        "candidate": candidate_name,
                        "status": reply_response.status_code,
                        "dry_run": reply_response.dry_run,
                        "closed_after": closed_after,
                    },
                )
                if candidate_success:
                    update_success = candidate_name
                    break
            return update_success

        if is_email_channel:
            author_id, bot_agent_id_source = _resolve_bot_agent_id(
                env_name=env_name, allow_network=allow_network
            )
            author_hash = _hash_identifier(author_id)
            if author_id:
                LOGGER.info(
                    "automation.order_status_reply.author_resolved",
                    extra={
                        "event_id": envelope.event_id,
                        "conversation_id": envelope.conversation_id,
                        "bot_agent_id_source": bot_agent_id_source,
                        "author_id_hash": author_hash,
                        "channel_detected": channel_detected,
                        "channel_detection_source": channel_detection_source,
                    },
                )
            else:
                LOGGER.info(
                    "automation.order_status_reply.author_missing",
                    extra={
                        "event_id": envelope.event_id,
                        "conversation_id": envelope.conversation_id,
                        "bot_agent_id_source": bot_agent_id_source,
                        "channel_detected": channel_detected,
                        "channel_detection_source": channel_detection_source,
                    },
                )
                result = _route_email_support(
                    "missing_bot_agent_id", ticket_status=ticket_status
                )
                result["blocked_reason"] = "missing_bot_agent_id"
                result.update(_metadata())
                if openai_rewrite is not None:
                    result["openai_rewrite"] = openai_rewrite
                return result

            send_response = executor.execute(
                "PUT",
                f"/v1/tickets/{encoded_id}/send-message",
                json_body={"author_id": author_id, "body": reply_body},
                dry_run=not allow_network,
            )
            responses.append(
                {
                    "action": "send_message",
                    "status": send_response.status_code,
                    "dry_run": send_response.dry_run,
                }
            )
            if send_response.dry_run:
                result = {
                    "sent": False,
                    "reason": "send_message_dry_run",
                    "responses": responses,
                    **_metadata(),
                }
                if openai_rewrite is not None:
                    result["openai_rewrite"] = openai_rewrite
                return result
            if send_response.status_code < 200 or send_response.status_code >= 300:
                result = _route_email_support(
                    "send_message_failed", ticket_status=ticket_status
                )
                result.update(_metadata())
                if openai_rewrite is not None:
                    result["openai_rewrite"] = openai_rewrite
                return result

            latest_comment_is_operator = _safe_ticket_comment_operator_fetch(
                target_id, executor=executor, allow_network=allow_network
            )
            responses.append(
                {
                    "action": "verify_send_message_operator",
                    "latest_comment_is_operator": latest_comment_is_operator,
                }
            )
            if latest_comment_is_operator is not True:
                result = _route_email_support(
                    "send_message_operator_missing",
                    ticket_status=ticket_status,
                    extra_tags=[
                        loop_prevention_tag,
                        ORDER_STATUS_REPLY_TAG,
                        REPLY_SENT_TAG,
                        run_specific_reply_tag,
                        OUTBOUND_PATH_SEND_MESSAGE_TAG,
                    ],
                )
                result.update(_metadata())
                if openai_rewrite is not None:
                    result["openai_rewrite"] = openai_rewrite
                return result

            update_success = _apply_update_candidates(
                close_candidates, strip_comment_after_success=False
            )
            if update_success is None:
                result = _route_email_support(
                    "reply_close_failed",
                    ticket_status=ticket_status,
                    extra_tags=[
                        loop_prevention_tag,
                        ORDER_STATUS_REPLY_TAG,
                        REPLY_SENT_TAG,
                        run_specific_reply_tag,
                        OUTBOUND_PATH_SEND_MESSAGE_TAG,
                    ],
                )
                result.update(_metadata())
                if openai_rewrite is not None:
                    result["openai_rewrite"] = openai_rewrite
                return result

            tags_to_apply = sorted(
                dedupe_tags(
                    [
                        loop_prevention_tag,
                        ORDER_STATUS_REPLY_TAG,
                        REPLY_SENT_TAG,
                        run_specific_reply_tag,
                        OUTBOUND_PATH_SEND_MESSAGE_TAG,
                    ]
                )
            )
            tag_response = executor.execute(
                "PUT",
                f"/v1/tickets/{encoded_id}/add-tags",
                json_body={"tags": tags_to_apply},
                dry_run=not allow_network,
            )
            responses.append(
                {
                    "action": "add_tag",
                    "status": tag_response.status_code,
                    "dry_run": tag_response.dry_run,
                }
            )

            LOGGER.info(
                "automation.order_status_reply.sent",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                    "statuses": [
                        entry["status"] for entry in responses if "status" in entry
                    ],
                    "dry_run": any(entry.get("dry_run") for entry in responses),
                    "loop_tag": loop_prevention_tag,
                    "update_candidate": update_success,
                    "outbound_path": "send_message",
                    "channel_detected": channel_detected,
                    "channel_detection_source": channel_detection_source,
                    "bot_agent_id_source": bot_agent_id_source,
                },
            )
            result = {
                "sent": True,
                "reason": "sent",
                "responses": responses,
                **_metadata(),
            }
            if openai_rewrite is not None:
                result["openai_rewrite"] = openai_rewrite
            return result

        update_success = _apply_update_candidates(
            update_candidates, strip_comment_after_success=True
        )
        if update_success is None:
            result = {
                "sent": False,
                "reason": "reply_update_failed",
                "responses": responses,
                **_metadata(),
            }
            if openai_rewrite is not None:
                result["openai_rewrite"] = openai_rewrite
            return result

        tags_to_apply = sorted(
            dedupe_tags(
                [
                    loop_prevention_tag,
                    ORDER_STATUS_REPLY_TAG,
                    REPLY_SENT_TAG,
                    run_specific_reply_tag,
                    OUTBOUND_PATH_COMMENT_TAG,
                ]
            )
        )
        tag_response = executor.execute(
            "PUT",
            f"/v1/tickets/{encoded_id}/add-tags",
            json_body={"tags": tags_to_apply},
            dry_run=not allow_network,
        )
        responses.append(
            {
                "action": "add_tag",
                "status": tag_response.status_code,
                "dry_run": tag_response.dry_run,
            }
        )

        LOGGER.info(
            "automation.order_status_reply.sent",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
                "statuses": [
                    entry["status"] for entry in responses if "status" in entry
                ],
                "dry_run": any(entry.get("dry_run") for entry in responses),
                "loop_tag": loop_prevention_tag,
                "update_candidate": update_success,
                "outbound_path": "comment",
                "channel_detected": channel_detected,
                "channel_detection_source": channel_detection_source,
                "bot_agent_id_source": bot_agent_id_source,
            },
        )
        result = {
            "sent": True,
            "reason": "sent",
            "responses": responses,
            **_metadata(),
        }
        if openai_rewrite is not None:
            result["openai_rewrite"] = openai_rewrite
        return result
    except (RichpanelRequestError, SecretLoadError, TransportError):
        LOGGER.exception(
            "automation.order_status_reply.failed",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
            },
        )
        result = {
            "sent": False,
            "reason": "exception",
            **_metadata(),
        }
        if openai_rewrite is not None:
            result["openai_rewrite"] = openai_rewrite
        return result


def _routing_tags_block_reason(
    *,
    outbound_enabled: bool,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    has_routing: bool,
    has_tags: bool,
) -> Optional[str]:
    if not outbound_enabled:
        return "outbound_disabled"
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
    if not allow_network:
        return "network_disabled"
    if not has_routing:
        return "missing_routing"
    if not has_tags:
        return "missing_routing_tags"
    return None


def execute_routing_tags(
    envelope: EventEnvelope,
    plan: ActionPlan,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
    richpanel_executor: Optional[RichpanelExecutor] = None,
    routing_applied_tag: str = ROUTING_APPLIED_TAG,
) -> Dict[str, Any]:
    """
    Apply routing tags to the Richpanel ticket so Richpanel automations can route it.

    Safe-by-default / fail-closed:
    - requires outbound_enabled, safe_mode == False, automation_enabled == True, allow_network == True
    - requires a routing decision with tags
    - uses the known Richpanel add-tags endpoint (no department assignment endpoints)
    """
    routing = plan.routing
    tags = sorted(dedupe_tags(getattr(routing, "tags", None) if routing else None))
    if routing_applied_tag and routing_applied_tag not in tags:
        tags.insert(0, routing_applied_tag)

    reason = _routing_tags_block_reason(
        outbound_enabled=outbound_enabled,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        has_routing=routing is not None,
        has_tags=bool(tags),
    )
    if reason:
        LOGGER.info(
            "automation.routing_tags.skip",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
                "reason": reason,
                "outbound_enabled": outbound_enabled,
                "allow_network": allow_network,
            },
        )
        return {"applied": False, "reason": reason}

    executor = richpanel_executor or RichpanelExecutor(
        outbound_enabled=outbound_enabled
        and allow_network
        and automation_enabled
        and not safe_mode
    )

    target_id = _resolve_target_ticket_id(
        envelope, executor=executor, allow_network=allow_network
    )
    encoded_id = urllib.parse.quote(str(target_id), safe="")

    try:
        response = executor.execute(
            "PUT",
            f"/v1/tickets/{encoded_id}/add-tags",
            json_body={"tags": tags},
            dry_run=not allow_network,
        )
        LOGGER.info(
            "automation.routing_tags.applied",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
                "status": response.status_code,
                "dry_run": response.dry_run,
                "tag_count": len(tags),
            },
        )
        return {
            "applied": True,
            "reason": "applied",
            "status": response.status_code,
            "dry_run": response.dry_run,
            "tag_count": len(tags),
        }
    except (RichpanelRequestError, SecretLoadError, TransportError):
        LOGGER.exception(
            "automation.routing_tags.failed",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
            },
        )
        return {"applied": False, "reason": "exception"}
