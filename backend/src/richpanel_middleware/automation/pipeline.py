from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from richpanel_middleware.ingest.envelope import EventEnvelope, normalize_envelope


@dataclass
class ActionPlan:
    """Structured representation of what the worker intends to do."""

    event_id: str
    mode: str
    safe_mode: bool
    automation_enabled: bool
    actions: List[Dict[str, Any]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Outcome of the execute step (dry-run by default)."""

    event_id: str
    mode: str
    dry_run: bool
    actions: List[Dict[str, Any]]
    state_record: Dict[str, Any]
    audit_record: Dict[str, Any]


def normalize_event(raw_event: Dict[str, Any]) -> EventEnvelope:
    """Normalize raw event payload into the canonical envelope."""
    return normalize_envelope(raw_event)


def plan_actions(
    envelope: EventEnvelope, *, safe_mode: bool, automation_enabled: bool
) -> ActionPlan:
    """
    Build a minimal action plan from the normalized envelope.

    In v1 the plan is intentionally conservative and dry-run only.
    """
    effective_automation = automation_enabled and not safe_mode
    mode = "automation_candidate" if effective_automation else "route_only"

    reasons: List[str] = []
    if safe_mode:
        reasons.append("safe_mode")
    if not automation_enabled:
        reasons.append("automation_disabled")

    actions: List[Dict[str, Any]] = []
    if mode == "route_only":
        actions.append(
            {
                "type": "route_only",
                "conversation_id": envelope.conversation_id,
                "note": "automation disabled; dry-run logging only",
                "reasons": reasons,
            }
        )
    else:
        actions.append(
            {
                "type": "analyze",
                "conversation_id": envelope.conversation_id,
                "note": "automation candidate (dry-run)",
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

    if state_writer:
        state_writer(state_record)
    if audit_writer:
        audit_writer(audit_record)

    return ExecutionResult(
        event_id=envelope.event_id,
        mode=plan.mode,
        dry_run=dry_run,
        actions=plan.actions,
        state_record=state_record,
        audit_record=audit_record,
    )
