from __future__ import annotations

import hashlib
import json
import logging
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

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

LOGGER = logging.getLogger(__name__)
LOOP_PREVENTION_TAG = "mw-auto-replied"
ORDER_STATUS_REPLY_TAG = "mw-order-status-answered"
ROUTING_APPLIED_TAG = "mw-routing-applied"
EMAIL_SUPPORT_ROUTE_TAG = "route-email-support-team"
ESCALATION_TAG = "mw-escalated-human"
REPLY_SENT_TAG = "mw-reply-sent"
SKIP_RESOLVED_TAG = "mw-skip-order-status-closed"
SKIP_FOLLOWUP_TAG = "mw-skip-followup-after-auto-reply"
SKIP_STATUS_READ_FAILED_TAG = "mw-skip-status-read-failed"
ORDER_LOOKUP_FAILED_TAG = "mw-order-lookup-failed"
ORDER_STATUS_SUPPRESSED_TAG = "mw-order-status-suppressed"
ORDER_LOOKUP_MISSING_PREFIX = "mw-order-lookup-missing"
# Follow-up after auto-reply should route to support without escalation.
_ESCALATION_REASONS: set[str] = set()
_SKIP_REASON_TAGS = {
    "already_resolved": SKIP_RESOLVED_TAG,
    "followup_after_auto_reply": SKIP_FOLLOWUP_TAG,
    "status_read_failed": SKIP_STATUS_READ_FAILED_TAG,
}


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
    routing, routing_artifact = compute_dual_routing(
        payload,
        conversation_id=envelope.conversation_id,
        event_id=envelope.event_id,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
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
) -> Optional[str]:
    if not outbound_enabled:
        return "outbound_disabled"
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
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
    reason = _outbound_block_reason(
        outbound_enabled=outbound_enabled,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        has_action=order_action is not None,
    )
    if reason and reason != "missing_order_status_action":
        LOGGER.info(
            "automation.order_status_reply.skip",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
                "reason": reason,
                "outbound_enabled": outbound_enabled,
                "allow_network": allow_network,
            },
        )
        return {"sent": False, "reason": reason}

    executor = richpanel_executor or RichpanelExecutor(
        outbound_enabled=outbound_enabled
        and allow_network
        and automation_enabled
        and not safe_mode
    )

    responses: List[Dict[str, Any]] = []
    openai_rewrite: Optional[Dict[str, Any]] = None
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

        ticket_metadata = _safe_ticket_metadata_fetch(
            target_id,
            executor=executor,
            allow_network=allow_network,
        )

        def _route_email_support(
            reason: str, ticket_status: Optional[str] = None
        ) -> Dict[str, Any]:
            route_tags = [EMAIL_SUPPORT_ROUTE_TAG]
            skip_tag = _SKIP_REASON_TAGS.get(reason)
            if skip_tag:
                route_tags.append(skip_tag)
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
            return _route_email_support("status_read_failed")

        ticket_status = ticket_metadata.status

        if loop_prevention_tag in (ticket_metadata.tags or set()):
            # Route follow-ups after auto-reply to Email Support Team (no duplicate reply,
            # no escalation). Preserve loop-prevention tag to avoid repeated replies,
            # even if the ticket is already closed.
            return _route_email_support(
                "followup_after_auto_reply", ticket_status=ticket_status
            )

        if order_action is None:
            LOGGER.info(
                "automation.order_status_reply.skip",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                    "reason": "missing_order_status_action",
                },
            )
            return {"sent": False, "reason": "missing_order_status_action"}

        if _is_closed_status(ticket_status):
            return _route_email_support("already_resolved", ticket_status=ticket_status)

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
            return {"sent": False, "reason": "missing_draft_reply"}

        original_hash = _fingerprint_reply_body(reply_body)
        rewrite_result: ReplyRewriteResult | None = None
        openai_rewrite: Dict[str, Any]
        try:
            rewrite_result = rewrite_reply(
                reply_body,
                conversation_id=envelope.conversation_id,
                event_id=envelope.event_id,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
                outbound_enabled=outbound_enabled,
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

        update_success = None
        comment_sent = False
        for candidate_name, payload in update_candidates:
            payload_dict = cast(Dict[str, Any], payload)
            payload_to_send: Dict[str, Any] = payload_dict
            if comment_sent:
                payload_to_send = _strip_comment(payload_dict)
            reply_response = executor.execute(
                "PUT",
                f"/v1/tickets/{encoded_id}",
                json_body=payload_to_send,
                dry_run=not allow_network,
            )
            candidate_success = (
                200 <= reply_response.status_code < 300 and not reply_response.dry_run
            )
            if candidate_success and _payload_has_comment(payload_to_send):
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

        if update_success is None:
            result = {
                "sent": False,
                "reason": "reply_update_failed",
                "responses": responses,
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
            },
        )
        result = {"sent": True, "reason": "sent", "responses": responses}
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
        result = {"sent": False, "reason": "exception"}
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
