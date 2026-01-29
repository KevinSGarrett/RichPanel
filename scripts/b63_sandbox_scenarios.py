#!/usr/bin/env python3
"""
b63_sandbox_scenarios.py

One-command sandbox scenario harness for B63:
- golden_path
- non_order_status
- order_status_no_match
- order_status_order_number
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sandbox_scenario_utils import (  # type: ignore
    _ensure_parent,
    _extract_ticket_ref,
    _fingerprint,
    _git_diffstat,
    _iso_timestamp,
    _read_proof,
    _redact_command,
    _run_command,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
DEFAULT_ARTIFACT_DIR = ROOT / "REHYDRATION_PACK" / "RUNS" / "B63" / "A"

_ORDER_STATUS_INTENTS = {
    "order_status_tracking",
    "shipping_delay_not_shipped",
    "order_status_no_tracking",
}


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_key: str
    smoke_scenario: str
    ticket_subject: str
    ticket_body: str
    proof_filename: str
    require_openai: bool = False
    require_order_match_by_number: bool = False
    require_outbound: bool = False
    require_send_message: bool = False
    require_operator_reply: bool = False
    order_number: Optional[str] = None
    order_number_fingerprint: Optional[str] = None


def _seed_order_number(seed: str) -> str:
    digest = _fingerprint(seed, length=10).upper()
    return f"FAKE-{digest}"


def _normalize_order_number(value: str) -> str:
    return str(value).strip().lstrip("#")


def _normalize_status(status: Optional[str]) -> Optional[str]:
    if not isinstance(status, str):
        return None
    value = status.strip().lower()
    return value or None


def _is_closed_status(status: Optional[str]) -> Optional[bool]:
    normalized = _normalize_status(status)
    if not normalized:
        return None
    return normalized in {"resolved", "closed"}


def _build_scenario_spec(args: argparse.Namespace, *, run_id: str) -> ScenarioSpec:
    key = args.scenario
    if key == "golden_path":
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="order_status",
            ticket_subject="Sandbox E2E B63 Golden Path",
            ticket_body="Where is my order? Please share the tracking update.",
            proof_filename="sandbox_golden_path_proof.json",
            require_openai=True,
            require_order_match_by_number=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            order_number=_normalize_order_number(args.order_number)
            if args.order_number
            else None,
            order_number_fingerprint=_fingerprint(_normalize_order_number(args.order_number))
            if args.order_number
            else None,
        )
    if key == "non_order_status":
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="not_order_status",
            ticket_subject="Sandbox E2E B63 Non-Order-Status",
            ticket_body="Please cancel my subscription and stop future charges.",
            proof_filename="sandbox_non_order_status_proof.json",
        )
    if key == "order_status_no_match":
        fake_order = _seed_order_number(run_id or "order-status-no-match")
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="order_status_no_match",
            ticket_subject="Sandbox E2E B63 Order Status No Match",
            ticket_body=f"Where is my order #{fake_order}? I need a status update.",
            proof_filename="sandbox_order_status_no_match_proof.json",
        )
    if key == "order_status_order_number":
        if not args.order_number:
            raise SystemExit("--order-number is required for order_status_order_number.")
        normalized = _normalize_order_number(args.order_number)
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="order_status",
            ticket_subject="Sandbox E2E B63 Order Status Order Number",
            ticket_body=(
                "Where is my order "
                f"#{normalized}? I need a status update with tracking details."
            ),
            proof_filename="sandbox_order_status_order_number_proof.json",
            require_order_match_by_number=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            order_number=normalized,
            order_number_fingerprint=_fingerprint(normalized),
        )
    raise SystemExit(f"Unsupported scenario: {key}")


def _proof_excerpt(proof: Optional[Dict[str, Any]]) -> str:
    if not proof:
        return json.dumps({"error": "proof not available"}, indent=2)
    fields = proof.get("proof_fields", {}) if isinstance(proof, dict) else {}
    richpanel = proof.get("richpanel", {}) if isinstance(proof, dict) else {}
    excerpt = {
        "intent_after": fields.get("intent_after"),
        "openai_routing_used": fields.get("openai_routing_used"),
        "openai_rewrite_used": fields.get("openai_rewrite_used"),
        "order_match_success": fields.get("order_match_success"),
        "order_match_by_number": fields.get("order_match_by_number"),
        "order_match_failure_reason": fields.get("order_match_failure_reason"),
        "outbound_attempted": fields.get("outbound_attempted"),
        "outbound_send_message_status": fields.get("outbound_send_message_status"),
        "send_message_path_confirmed": fields.get("send_message_path_confirmed"),
        "operator_reply_confirmed": fields.get("operator_reply_confirmed"),
        "closed_after": fields.get("closed_after"),
        "status_after": richpanel.get("status_after") if isinstance(richpanel, dict) else None,
        "routed_to_support": fields.get("routed_to_support"),
        "support_tag_present": fields.get("support_tag_present"),
        "support_department": fields.get("support_department"),
        "reply_contains_tracking_url": fields.get("reply_contains_tracking_url"),
        "reply_contains_tracking_number_like": fields.get(
            "reply_contains_tracking_number_like"
        ),
        "reply_contains_eta_date_like": fields.get("reply_contains_eta_date_like"),
    }
    return json.dumps(excerpt, indent=2)


def _write_run_report(
    path: Path,
    *,
    scenario_key: str,
    proof: Optional[Dict[str, Any]],
    error: Optional[str],
    order_number_fingerprint: Optional[str],
) -> None:
    _ensure_parent(path)
    result = proof.get("result", {}) if isinstance(proof, dict) else {}
    fields = proof.get("proof_fields", {}) if isinstance(proof, dict) else {}
    inputs = proof.get("inputs", {}) if isinstance(proof, dict) else {}
    status = result.get("status") if isinstance(result, dict) else None
    classification = result.get("classification") if isinstance(result, dict) else None
    failure_reason = result.get("failure_reason") if isinstance(result, dict) else None
    classification_reason = (
        result.get("classification_reason") if isinstance(result, dict) else None
    )
    ticket_fingerprint = inputs.get("ticket_ref_fingerprint")
    outbound_failure = fields.get("outbound_failure_classification")
    lines = [
        "# Run Report — B63/A",
        "",
        f"- Timestamp: `{_iso_timestamp()}`",
        f"- Scenario: `{scenario_key}`",
        f"- Status: `{status or 'UNKNOWN'}`",
        f"- Classification: `{classification or 'unknown'}`",
        f"- Failure reason: `{failure_reason or classification_reason or 'none'}`",
        f"- Ticket fingerprint: `{ticket_fingerprint or 'n/a'}`",
        f"- Order number fingerprint: `{order_number_fingerprint or 'n/a'}`",
        f"- Outbound failure: `{outbound_failure or 'n/a'}`",
    ]
    if error:
        lines.append(f"- Error: `{error}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_evidence(
    path: Path,
    *,
    root: Path,
    wrapper_cmd: List[str],
    create_cmds: List[List[str]],
    recent_cmds: List[List[str]],
    smoke_cmds: List[List[str]],
    proof: Optional[Dict[str, Any]],
) -> None:
    _ensure_parent(path)
    lines = [
        "# Evidence — B63/A",
        "",
        "## Scope and safety",
        "- Sandbox/dev only; no production writes.",
        "- All values PII-safe; use `<redacted>` for any real emails or ticket refs.",
        "",
        "## Command (one-command harness)",
        "```powershell",
        f"cd {root}",
        _redact_command(wrapper_cmd),
        "```",
    ]
    if create_cmds:
        lines.extend(["", "## Internal command — create ticket"])
        for idx, cmd in enumerate(create_cmds, start=1):
            lines.extend(
                [
                    f"### Attempt {idx}",
                    "```powershell",
                    f"cd {root}",
                    _redact_command(cmd),
                    "```",
                ]
            )
    if recent_cmds:
        lines.extend(["", "## Internal command — find recent ticket"])
        for idx, cmd in enumerate(recent_cmds, start=1):
            lines.extend(
                [
                    f"### Attempt {idx}",
                    "```powershell",
                    f"cd {root}",
                    _redact_command(cmd),
                    "```",
                ]
            )
    if smoke_cmds:
        lines.extend(["", "## Internal command — smoke proof"])
        for idx, cmd in enumerate(smoke_cmds, start=1):
            lines.extend(
                [
                    f"### Attempt {idx}",
                    "```powershell",
                    f"cd {root}",
                    _redact_command(cmd),
                    "```",
                ]
            )
    lines.extend(
        [
            "",
            "## Proof excerpt (PII-safe)",
            "```json",
            _proof_excerpt(proof),
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_changes(path: Path) -> None:
    _ensure_parent(path)
    diffstat = _git_diffstat(ROOT)
    lines = [
        "# Changes — B63/A",
        "",
        "## Intent",
        "- Add B63 sandbox scenario wrapper and proof templates.",
        "- Extend sandbox E2E coverage for negative/no-match/order-number cases.",
        "",
        "## Diffstat",
        "```",
        diffstat or "(no changes)",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_scenario_assertions(
    proof: Dict[str, Any],
    *,
    scenario_key: str,
    order_number_fingerprint: Optional[str],
) -> Tuple[str, Optional[str]]:
    fields = proof.get("proof_fields", {}) if isinstance(proof, dict) else {}
    richpanel = proof.get("richpanel", {}) if isinstance(proof, dict) else {}
    status_after = None
    if isinstance(richpanel, dict):
        status_after = richpanel.get("status_after")
    closed_after = _is_closed_status(status_after)
    intent_after = fields.get("intent_after")
    outbound_attempted = fields.get("outbound_attempted")
    routed_to_support = fields.get("routed_to_support")
    order_match_success = fields.get("order_match_success")
    order_match_failure = fields.get("order_match_failure_reason")
    order_match_by_number = fields.get("order_match_by_number")
    operator_reply_confirmed = fields.get("operator_reply_confirmed")
    send_message_path_confirmed = fields.get("send_message_path_confirmed")
    reply_tracking_url = fields.get("reply_contains_tracking_url")
    reply_tracking_number = fields.get("reply_contains_tracking_number_like")

    checks: List[Dict[str, Any]] = []

    def add_check(name: str, value: Optional[bool], required: bool, description: str) -> None:
        checks.append(
            {
                "name": name,
                "description": description,
                "required": required,
                "value": value,
            }
        )

    if scenario_key == "golden_path":
        add_check(
            "order_match_by_number",
            order_match_by_number is True if order_match_by_number is not None else None,
            True,
            "Order match resolved by order number.",
        )
        add_check(
            "outbound_attempted",
            outbound_attempted is True if outbound_attempted is not None else None,
            True,
            "Outbound reply attempt observed.",
        )
        add_check(
            "send_message_path_confirmed",
            send_message_path_confirmed is True
            if send_message_path_confirmed is not None
            else None,
            True,
            "Send-message path tag confirmed.",
        )
        add_check(
            "operator_reply_confirmed",
            operator_reply_confirmed is True
            if operator_reply_confirmed is not None
            else None,
            True,
            "Operator reply confirmed on latest comment.",
        )
        add_check(
            "closed_after",
            closed_after is True if closed_after is not None else None,
            True,
            "Ticket closed/resolved after reply.",
        )
    elif scenario_key == "non_order_status":
        intent_not_order_status = None
        if isinstance(intent_after, str):
            intent_not_order_status = intent_after not in _ORDER_STATUS_INTENTS
        add_check(
            "intent_not_order_status",
            intent_not_order_status,
            True,
            "Routing intent is not order-status.",
        )
        add_check(
            "no_outbound_attempt",
            outbound_attempted is False if outbound_attempted is not None else None,
            True,
            "No outbound reply attempt detected.",
        )
        add_check(
            "routed_to_support",
            routed_to_support is True if routed_to_support is not None else None,
            True,
            "Ticket routed to support queue.",
        )
        add_check(
            "not_auto_closed",
            closed_after is False if closed_after is not None else None,
            True,
            "Ticket not auto-closed by order-status automation.",
        )
    elif scenario_key == "order_status_no_match":
        intent_order_status = None
        if isinstance(intent_after, str):
            intent_order_status = intent_after in _ORDER_STATUS_INTENTS
        add_check(
            "intent_order_status",
            intent_order_status,
            True,
            "Routing intent matches order-status.",
        )
        add_check(
            "order_match_failed",
            order_match_success is False if order_match_success is not None else None,
            True,
            "Order match failed as expected.",
        )
        add_check(
            "order_match_failure_reason_present",
            bool(order_match_failure) if order_match_failure is not None else None,
            True,
            "Order match failure reason recorded.",
        )
        add_check(
            "no_outbound_attempt",
            outbound_attempted is False if outbound_attempted is not None else None,
            True,
            "No outbound reply attempt detected.",
        )
        add_check(
            "routed_to_support",
            routed_to_support is True if routed_to_support is not None else None,
            True,
            "Ticket routed to support queue.",
        )
    elif scenario_key == "order_status_order_number":
        add_check(
            "order_match_by_number",
            order_match_by_number is True if order_match_by_number is not None else None,
            True,
            "Order match resolved by order number.",
        )
        add_check(
            "outbound_attempted",
            outbound_attempted is True if outbound_attempted is not None else None,
            True,
            "Outbound reply attempt observed.",
        )
        add_check(
            "send_message_path_confirmed",
            send_message_path_confirmed is True
            if send_message_path_confirmed is not None
            else None,
            True,
            "Send-message path tag confirmed.",
        )
        add_check(
            "operator_reply_confirmed",
            operator_reply_confirmed is True
            if operator_reply_confirmed is not None
            else None,
            True,
            "Operator reply confirmed on latest comment.",
        )
        add_check(
            "closed_after",
            closed_after is True if closed_after is not None else None,
            True,
            "Ticket closed/resolved after reply.",
        )
        tracking_ok = None
        if isinstance(reply_tracking_url, bool) or isinstance(reply_tracking_number, bool):
            tracking_ok = bool(reply_tracking_url) or bool(reply_tracking_number)
        add_check(
            "reply_contains_tracking",
            tracking_ok,
            True,
            "Reply includes tracking URL or tracking number.",
        )

    required_failed = [
        entry["name"]
        for entry in checks
        if entry.get("required") and not entry.get("value")
    ]
    status = "PASS" if not required_failed else "FAIL"
    failure_reason = (
        f"Failed checks: {', '.join(required_failed)}" if required_failed else None
    )

    proof["scenario_assertions"] = {
        "scenario": scenario_key,
        "order_number_fingerprint": order_number_fingerprint,
        "status": status,
        "failure_reason": failure_reason,
        "checks": checks,
    }
    return status, failure_reason


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the B63 sandbox scenario harness."
    )
    parser.add_argument(
        "--scenario",
        choices=[
            "golden_path",
            "non_order_status",
            "order_status_no_match",
            "order_status_order_number",
        ],
        required=True,
        help="Scenario to run.",
    )
    parser.add_argument("--env", default="dev", help="Target environment (default: dev).")
    parser.add_argument("--region", required=True, help="AWS region (e.g. us-east-2).")
    parser.add_argument(
        "--stack-name",
        default="RichpanelMiddleware-dev",
        help="CloudFormation stack name.",
    )
    parser.add_argument("--profile", help="Optional AWS profile name.")
    parser.add_argument("--run-id", help="Run identifier for proof attribution.")
    parser.add_argument(
        "--allowlist-email",
        help="Allowlisted test recipient to use as the ticket from-email.",
    )
    parser.add_argument("--ticket-number", help="Use existing ticket number (skip creation).")
    parser.add_argument("--ticket-id", help="Use existing ticket ID (skip creation).")
    parser.add_argument(
        "--order-number",
        help="Order number to embed for order-number match scenario.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        help="Override how long dev_e2e_smoke waits for ticket updates.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=str(DEFAULT_ARTIFACT_DIR),
        help="Directory for run artifacts.",
    )
    parser.add_argument(
        "--proof-path",
        help="Override path to write proof JSON (defaults per scenario).",
    )
    return parser.parse_args()


def _build_smoke_cmd(
    args: argparse.Namespace,
    *,
    scenario: ScenarioSpec,
    proof_path: Path,
    run_id: str,
    ticket_number: Optional[str],
    ticket_id: Optional[str],
) -> List[str]:
    smoke_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "dev_e2e_smoke.py"),
        "--env",
        args.env,
        "--region",
        args.region,
        "--stack-name",
        args.stack_name,
        "--scenario",
        scenario.smoke_scenario,
        "--proof-path",
        str(proof_path),
        "--run-id",
        run_id,
    ]
    if args.profile:
        smoke_cmd.extend(["--profile", args.profile])
    if scenario.require_openai:
        smoke_cmd.extend(["--require-openai-routing", "--require-openai-rewrite"])
    else:
        smoke_cmd.extend(["--no-require-openai-routing", "--no-require-openai-rewrite"])
    if scenario.require_order_match_by_number:
        smoke_cmd.append("--require-order-match-by-number")
    if scenario.require_outbound:
        smoke_cmd.append("--require-outbound")
    if scenario.require_send_message:
        smoke_cmd.append("--require-send-message")
    if scenario.require_operator_reply:
        smoke_cmd.append("--require-operator-reply")
    if scenario.order_number:
        smoke_cmd.extend(["--order-number", scenario.order_number])
    if args.wait_seconds:
        smoke_cmd.extend(["--wait-seconds", str(args.wait_seconds)])
    if ticket_number:
        smoke_cmd.extend(["--ticket-number", ticket_number])
    elif ticket_id:
        smoke_cmd.extend(["--ticket-id", ticket_id])
    return smoke_cmd


def main() -> int:
    args = parse_args()
    artifacts_dir = Path(args.artifacts_dir)
    run_id = (
        args.run_id
        or os.environ.get("RUN_ID")
        or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    )
    scenario = _build_scenario_spec(args, run_id=run_id)
    proof_path = (
        Path(args.proof_path)
        if args.proof_path
        else artifacts_dir / "PROOF" / scenario.proof_filename
    )
    created_ticket_path = (
        artifacts_dir / "PROOF" / f"created_ticket_{scenario.scenario_key}.json"
    )
    run_report_path = artifacts_dir / "RUN_REPORT.md"
    evidence_path = artifacts_dir / "EVIDENCE.md"
    changes_path = artifacts_dir / "CHANGES.md"

    wrapper_cmd = [sys.executable, str(Path(__file__).resolve())] + sys.argv[1:]
    create_cmds: List[List[str]] = []
    recent_cmds: List[List[str]] = []
    smoke_cmds: List[List[str]] = []
    proof: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    ticket_number = args.ticket_number
    ticket_id = args.ticket_id

    try:
        explicit_ticket = bool(ticket_number or ticket_id)
        max_attempts = 1 if explicit_ticket else 3
        tried_refs: set[str] = set()
        last_failure: Optional[RuntimeError] = None

        for _attempt in range(1, max_attempts + 1):
            if not explicit_ticket:
                ticket_number = None
                ticket_id = None

                create_cmd = [
                    sys.executable,
                    str(SCRIPTS_DIR / "create_sandbox_email_ticket.py"),
                    "--env",
                    args.env,
                    "--region",
                    args.region,
                    "--stack-name",
                    args.stack_name,
                    "--proof-path",
                    str(created_ticket_path),
                    "--emit-ticket-ref",
                    "--subject",
                    scenario.ticket_subject,
                    "--body",
                    scenario.ticket_body,
                ]
                if args.profile:
                    create_cmd.extend(["--profile", args.profile])
                if args.allowlist_email:
                    create_cmd.extend(["--from-email", args.allowlist_email])
                create_cmds.append(create_cmd)
                create_result = _run_command(create_cmd)
                if create_result.returncode == 0:
                    ref = _extract_ticket_ref(create_result.stdout)
                    ticket_number = ref.get("ticket_number") or None
                    ticket_id = ref.get("ticket_id") or None

                if not ticket_number and not ticket_id:
                    recent_cmd = [
                        sys.executable,
                        str(SCRIPTS_DIR / "find_recent_sandbox_ticket.py"),
                        "--env",
                        args.env,
                        "--region",
                        args.region,
                        "--max-results",
                        "5",
                    ]
                    if args.profile:
                        recent_cmd.extend(["--profile", args.profile])
                    recent_cmds.append(recent_cmd)
                    recent_result = _run_command(recent_cmd)
                    if recent_result.returncode != 0:
                        raise RuntimeError(
                            "find_recent_sandbox_ticket.py failed while recovering from "
                            "ticket creation failure."
                        )
                    try:
                        recent_payload = json.loads(recent_result.stdout or "[]")
                    except json.JSONDecodeError as exc:
                        raise RuntimeError(
                            "Failed to parse recent ticket list JSON."
                        ) from exc
                    if not isinstance(recent_payload, list) or not recent_payload:
                        raise RuntimeError("No recent sandbox tickets found.")
                    recent = []
                    for entry in recent_payload:
                        if not isinstance(entry, dict):
                            continue
                        recent.append(
                            {
                                "ticket_number": entry.get("ticket_number"),
                                "ticket_id": entry.get("ticket_id"),
                            }
                        )
                    for entry in recent:
                        candidate = f"{entry.get('ticket_number')}|{entry.get('ticket_id')}"
                        if candidate in tried_refs:
                            continue
                        ticket_number = entry.get("ticket_number") or None
                        ticket_id = entry.get("ticket_id") or None
                        if ticket_number or ticket_id:
                            break

                if not ticket_number and not ticket_id:
                    raise RuntimeError(
                        "Ticket creation failed and no recent ticket could be located."
                    )

            if ticket_number or ticket_id:
                tried_refs.add(f"{ticket_number}|{ticket_id}")

            smoke_cmd = _build_smoke_cmd(
                args,
                scenario=scenario,
                proof_path=proof_path,
                run_id=run_id,
                ticket_number=ticket_number,
                ticket_id=ticket_id,
            )
            smoke_cmds.append(smoke_cmd)

            smoke_result = _run_command(smoke_cmd)
            if smoke_result.returncode == 0:
                last_failure = None
                break

            last_failure = RuntimeError(
                f"dev_e2e_smoke.py failed (exit={smoke_result.returncode})."
            )
            if explicit_ticket:
                raise last_failure
        if last_failure:
            raise last_failure
    except Exception as exc:
        error = str(exc)
    finally:
        proof = _read_proof(proof_path)
        assertion_status = None
        assertion_reason = None
        if proof and isinstance(proof, dict):
            assertion_status, assertion_reason = _append_scenario_assertions(
                proof,
                scenario_key=scenario.scenario_key,
                order_number_fingerprint=scenario.order_number_fingerprint,
            )
            proof_path.write_text(
                json.dumps(proof, indent=2) + "\n", encoding="utf-8"
            )
        if assertion_status == "FAIL" and not error:
            error = assertion_reason or "Scenario assertions failed."
        _write_run_report(
            run_report_path,
            scenario_key=scenario.scenario_key,
            proof=proof,
            error=error,
            order_number_fingerprint=scenario.order_number_fingerprint,
        )
        _write_evidence(
            evidence_path,
            root=ROOT,
            wrapper_cmd=wrapper_cmd,
            create_cmds=create_cmds,
            recent_cmds=recent_cmds,
            smoke_cmds=smoke_cmds,
            proof=proof,
        )
        _write_changes(changes_path)

    outbound_failure = None
    if proof and isinstance(proof.get("proof_fields"), dict):
        outbound_failure = proof["proof_fields"].get("outbound_failure_classification")
    if outbound_failure == "blocked_by_allowlist":
        hint_email = args.allowlist_email or "<allowlist test recipient>"
        print(
            "[ACTION] Outbound blocked by allowlist. For dev/sandbox only, "
            "set MW_OUTBOUND_ALLOWLIST_EMAILS to include "
            f"{hint_email} and re-run."
        )

    return 1 if error else 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
