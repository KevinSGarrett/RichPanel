from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from richpanel_middleware.automation.delivery_estimate import (
    build_no_tracking_reply,
    build_tracking_reply,
    compute_delivery_estimate,
)
from richpanel_middleware.automation.llm_routing import (
    LLMRoutingArtifact,
    compute_llm_routing_artifact,
)
from richpanel_middleware.automation.router import (
    RoutingDecision,
    classify_routing,
    extract_customer_message,
)
from richpanel_middleware.commerce.order_lookup import lookup_order_summary
from richpanel_middleware.integrations.richpanel.client import (
    RichpanelExecutor,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)
from richpanel_middleware.automation.prompts import (
    OrderStatusPromptInput,
    build_order_status_contract,
    prompt_fingerprint,
)
from richpanel_middleware.ingest.envelope import EventEnvelope, normalize_envelope

LOGGER = logging.getLogger(__name__)
LOOP_PREVENTION_TAG = "mw-auto-replied"
ROUTING_APPLIED_TAG = "mw-routing-applied"


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
    llm_routing_artifact: LLMRoutingArtifact | None = None


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


def plan_actions(
    envelope: EventEnvelope,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool = False,
) -> ActionPlan:
    """
    Build a minimal action plan from the normalized envelope.

    In v1 the plan is intentionally conservative and dry-run only.

    The deterministic router is the operational default.
    LLM routing suggestion is computed in advisory mode and persisted
    for audit/comparison (bridge from deterministic -> LLM-primary later).
    """
    # 1. Compute baseline deterministic route (operational)
    routing = classify_routing(envelope.payload)
    payload = envelope.payload if isinstance(envelope.payload, dict) else {}
    effective_automation = automation_enabled and not safe_mode
    mode = "automation_candidate" if effective_automation else "route_only"

    reasons: List[str] = []
    if safe_mode:
        reasons.append("safe_mode")
    if not automation_enabled:
        reasons.append("automation_disabled")
    reasons.append(routing.reason)

    # 2. Compute LLM routing suggestion (advisory only)
    # This is gated and will return a dry-run artifact if gates are not satisfied
    llm_routing_artifact = compute_llm_routing_artifact(
        payload,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
    )

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
                allow_network=False,
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
        llm_routing_artifact=llm_routing_artifact,
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
    state_record: Dict[str, Any] = {
        "conversation_id": envelope.conversation_id,
        "event_id": envelope.event_id,
        "mode": plan.mode,
        "actions": plan.actions,
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
        "actions": plan.actions,
        "reasons": plan.reasons,
        "dry_run": dry_run,
        "source": envelope.source,
    }
    if plan.routing:
        routing_dict = asdict(plan.routing)
        state_record["routing"] = routing_dict
        audit_record["routing"] = routing_dict

    # Persist LLM routing artifact (advisory mode)
    # This enables comparison between deterministic and LLM routing
    if plan.llm_routing_artifact:
        llm_artifact_dict = plan.llm_routing_artifact.to_dict()
        state_record["llm_routing_advisory"] = llm_artifact_dict
        audit_record["llm_routing_advisory"] = llm_artifact_dict

    if state_writer:
        state_writer(state_record)
    if audit_writer:
        audit_writer(audit_record)

    return ExecutionResult(
        event_id=envelope.event_id,
        mode=plan.mode,
        dry_run=dry_run,
        actions=plan.actions,
        routing=plan.routing
        if plan.routing
        else RoutingDecision(
            category="general",
            tags=[],
            reason="routing missing",
            department="Email Support Team",
            intent="unknown",
        ),
        state_record=state_record,
        audit_record=audit_record,
    )


def _find_order_status_action(plan: ActionPlan) -> Optional[Dict[str, Any]]:
    for action in plan.actions:
        if action.get("type") == "order_status_draft_reply":
            return action
    return None


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
    if reason:
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

    if order_action is None:
        return {"sent": False, "reason": "missing_order_status_action"}

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

    executor = richpanel_executor or RichpanelExecutor(
        outbound_enabled=outbound_enabled and allow_network and automation_enabled and not safe_mode
    )

    responses: List[Dict[str, Any]] = []
    try:
        tag_response = executor.execute(
            "PUT",
            f"/v1/tickets/{envelope.conversation_id}/add-tags",
            json_body={"tags": [loop_prevention_tag]},
            dry_run=not allow_network,
        )
        responses.append(
            {
                "action": "add_tag",
                "status": tag_response.status_code,
                "dry_run": tag_response.dry_run,
            }
        )

        reply_response = executor.execute(
            "PUT",
            f"/v1/tickets/{envelope.conversation_id}",
            json_body={
                "status": "resolved",
                "comment": {"body": reply_body, "type": "public", "source": "middleware"},
                "tags": [loop_prevention_tag],
            },
            dry_run=not allow_network,
        )
        responses.append(
            {
                "action": "reply_and_resolve",
                "status": reply_response.status_code,
                "dry_run": reply_response.dry_run,
            }
        )

        LOGGER.info(
            "automation.order_status_reply.sent",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
                "statuses": [entry["status"] for entry in responses],
                "dry_run": any(entry.get("dry_run") for entry in responses),
                "loop_tag": loop_prevention_tag,
            },
        )
        return {"sent": True, "reason": "sent", "responses": responses}
    except (RichpanelRequestError, SecretLoadError, TransportError):
        LOGGER.exception(
            "automation.order_status_reply.failed",
            extra={
                "event_id": envelope.event_id,
                "conversation_id": envelope.conversation_id,
            },
        )
        return {"sent": False, "reason": "exception"}


def _dedupe_tags(raw_tags: Any) -> List[str]:
    tags: List[str] = []
    if isinstance(raw_tags, list):
        candidates = raw_tags
    elif raw_tags is None:
        candidates = []
    else:
        candidates = [raw_tags]

    seen: set[str] = set()
    for candidate in candidates:
        try:
            value = str(candidate).strip()
        except Exception:
            continue
        if not value or value in seen:
            continue
        tags.append(value)
        seen.add(value)
    return tags


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
    tags = _dedupe_tags(getattr(routing, "tags", None) if routing else None)
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
        outbound_enabled=outbound_enabled and allow_network and automation_enabled and not safe_mode
    )

    try:
        response = executor.execute(
            "PUT",
            f"/v1/tickets/{envelope.conversation_id}/add-tags",
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


