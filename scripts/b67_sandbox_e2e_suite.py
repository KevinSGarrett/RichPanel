#!/usr/bin/env python3
"""
b67_sandbox_e2e_suite.py

Sandbox E2E suite wrapper for B67:
- order_status_golden
- order_status_fallback_email_match
- not_order_status_negative_case
- followup_after_autoclose
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
DEFAULT_ARTIFACT_DIR = ROOT / "REHYDRATION_PACK" / "RUNS" / "B67" / "A"
DEFAULT_PROOF_DIR = DEFAULT_ARTIFACT_DIR / "PROOF"
DEFAULT_SUITE_RESULTS = DEFAULT_PROOF_DIR / "sandbox_e2e_suite_results.json"
DEFAULT_SUITE_SUMMARY = DEFAULT_PROOF_DIR / "sandbox_e2e_suite_summary.md"

TICKET_REF_PREFIX = "TICKET_REF_JSON:"
SENSITIVE_FLAGS = {
    "--ticket-number",
    "--ticket-id",
    "--from-email",
    "--subject",
    "--body",
    "--ticket-from-email",
    "--ticket-subject",
    "--ticket-body",
    "--allowlist-email",
    "--order-number",
}

ORDER_STATUS_INTENTS = {
    "order_status_tracking",
    "shipping_delay_not_shipped",
    "order_status_no_tracking",
}

ENV_FLAG_KEYS = (
    "RICHPANEL_OUTBOUND_ENABLED",
    "RICHPANEL_BOT_AGENT_ID",
    "MW_OPENAI_INTENT_ENABLED",
    "MW_OPENAI_ROUTING_ENABLED",
)


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_key: str
    smoke_scenario: str
    ticket_subject: str
    ticket_body: str
    proof_filename: str
    require_openai_routing: bool = False
    require_openai_rewrite: bool = False
    require_order_match_by_number: bool = False
    require_outbound: bool = False
    require_send_message: bool = False
    require_operator_reply: bool = False
    followup: bool = False
    order_number: Optional[str] = None
    order_number_fingerprint: Optional[str] = None


@dataclass
class ScenarioRunResult:
    scenario_key: str
    proof_path: Path
    status: str
    error: Optional[str]
    proof: Optional[Dict[str, Any]]
    commands: List[List[str]]


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _fingerprint(value: str, length: int = 12) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _normalize_order_number(value: str) -> str:
    return str(value).strip().lstrip("#")


def _redact_command(cmd: List[str]) -> str:
    redacted: List[str] = []
    skip_next = False
    for part in cmd:
        if skip_next:
            redacted.append("<redacted>")
            skip_next = False
            continue
        if part in SENSITIVE_FLAGS:
            redacted.append(part)
            skip_next = True
            continue
        replaced = False
        for flag in SENSITIVE_FLAGS:
            prefix = f"{flag}="
            if part.startswith(prefix):
                redacted.append(f"{flag}=<redacted>")
                replaced = True
                break
        if not replaced:
            redacted.append(part)
    return " ".join(redacted)


def _run_command(
    cmd: List[str], *, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)


def _extract_ticket_ref(output: str) -> Dict[str, Optional[str]]:
    for line in output.splitlines():
        if line.startswith(TICKET_REF_PREFIX):
            payload = json.loads(line[len(TICKET_REF_PREFIX) :].strip())
            if isinstance(payload, dict):
                return {
                    "ticket_number": payload.get("ticket_number"),
                    "ticket_id": payload.get("ticket_id"),
                    "ticket_number_fingerprint": payload.get(
                        "ticket_number_fingerprint"
                    ),
                    "ticket_id_fingerprint": payload.get("ticket_id_fingerprint"),
                }
    raise RuntimeError("Missing ticket reference output from create_sandbox_email_ticket.py.")


def _read_proof(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _capture_env_flags() -> Dict[str, Optional[str]]:
    return {key: os.environ.get(key) for key in ENV_FLAG_KEYS}


def _build_scenario_spec(args: argparse.Namespace, *, run_id: str) -> ScenarioSpec:
    key = args.scenario
    if key == "order_status_golden":
        order_number = (
            _normalize_order_number(args.order_number) if args.order_number else None
        )
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="order_status",
            ticket_subject="Sandbox E2E B67 Order Status Golden",
            ticket_body="Where is my order? Please share the tracking update.",
            proof_filename="sandbox_order_status_golden_proof.json",
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_order_match_by_number=bool(order_number),
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            followup=False,
            order_number=order_number,
            order_number_fingerprint=_fingerprint(order_number) if order_number else None,
        )
    if key == "order_status_fallback_email_match":
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="order_status_fallback_email_match",
            ticket_subject="Sandbox E2E B67 Order Status Fallback",
            ticket_body="Hi, can you check the status of my order? Thanks!",
            proof_filename="sandbox_fallback_email_match_proof.json",
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
        )
    if key == "not_order_status_negative_case":
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="not_order_status",
            ticket_subject="Sandbox E2E B67 Refund Request",
            ticket_body="I want a refund for my last purchase. Please assist.",
            proof_filename="sandbox_negative_case_proof.json",
            require_openai_routing=True,
            require_openai_rewrite=False,
        )
    if key == "followup_after_autoclose":
        return ScenarioSpec(
            scenario_key=key,
            smoke_scenario="order_status",
            ticket_subject="Sandbox E2E B67 Follow-up Suppression",
            ticket_body="Where is my order? Please share the latest update.",
            proof_filename="sandbox_followup_suppression_proof.json",
            require_openai_routing=True,
            require_openai_rewrite=True,
            require_outbound=True,
            require_send_message=True,
            require_operator_reply=True,
            followup=True,
        )
    raise SystemExit(f"Unsupported scenario: {key}")


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
    if scenario.require_openai_routing:
        smoke_cmd.append("--require-openai-routing")
    else:
        smoke_cmd.append("--no-require-openai-routing")
    if scenario.require_openai_rewrite:
        smoke_cmd.append("--require-openai-rewrite")
    else:
        smoke_cmd.append("--no-require-openai-rewrite")
    if scenario.require_order_match_by_number:
        smoke_cmd.append("--require-order-match-by-number")
    if scenario.require_outbound:
        smoke_cmd.append("--require-outbound")
    if scenario.require_send_message:
        smoke_cmd.append("--require-send-message")
    if scenario.require_operator_reply:
        smoke_cmd.append("--require-operator-reply")
    if scenario.followup:
        smoke_cmd.extend(
            ["--followup", "--followup-message", str(args.followup_message)]
        )
    if scenario.order_number:
        smoke_cmd.extend(["--order-number", scenario.order_number])
    if args.wait_seconds:
        smoke_cmd.extend(["--wait-seconds", str(args.wait_seconds)])
    if ticket_number:
        smoke_cmd.extend(["--ticket-number", ticket_number])
    elif ticket_id:
        smoke_cmd.extend(["--ticket-id", ticket_id])
    return smoke_cmd


def _append_scenario_assertions(
    proof: Dict[str, Any],
    *,
    scenario: ScenarioSpec,
) -> Tuple[str, Optional[str]]:
    fields = proof.get("proof_fields", {}) if isinstance(proof, dict) else {}
    status_after = None
    if isinstance(proof.get("richpanel"), dict):
        status_after = proof["richpanel"].get("status_after")

    closed_after = None
    if isinstance(status_after, str):
        closed_after = status_after.strip().lower() in {"resolved", "closed"}

    intent_after = fields.get("intent_after")
    outbound_attempted = fields.get("outbound_attempted")
    routed_to_support = fields.get("routed_to_support")
    order_match_success = fields.get("order_match_success")
    order_match_by_number = fields.get("order_match_by_number")
    order_match_method = fields.get("order_match_method")
    operator_reply_confirmed = fields.get("operator_reply_confirmed")
    send_message_path_confirmed = fields.get("send_message_path_confirmed")
    followup_reply_sent = fields.get("followup_reply_sent")
    followup_routed_support = fields.get("followup_routed_support")

    checks: List[Dict[str, Any]] = []

    def add_check(
        name: str, value: Optional[bool], required: bool, description: str
    ) -> None:
        checks.append(
            {
                "name": name,
                "description": description,
                "required": required,
                "value": value,
            }
        )

    if scenario.scenario_key == "order_status_golden":
        if scenario.require_order_match_by_number:
            add_check(
                "order_match_by_number",
                order_match_by_number is True
                if order_match_by_number is not None
                else None,
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
            "Send-message path confirmed.",
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
    elif scenario.scenario_key == "order_status_fallback_email_match":
        intent_order_status = None
        if isinstance(intent_after, str):
            intent_order_status = intent_after in ORDER_STATUS_INTENTS
        add_check(
            "intent_order_status",
            intent_order_status,
            True,
            "Routing intent matches order-status.",
        )
        add_check(
            "order_match_success",
            order_match_success is True if order_match_success is not None else None,
            True,
            "Order match succeeded without order number.",
        )
        add_check(
            "order_match_method_email",
            order_match_method in {"email_only", "name_email"}
            if order_match_method is not None
            else None,
            True,
            "Order match method is email or name+email.",
        )
        add_check(
            "order_match_not_by_number",
            (order_match_method != "order_number")
            if order_match_method is not None
            else None,
            True,
            "Order match was not by order number.",
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
            "Send-message path confirmed.",
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
    elif scenario.scenario_key == "not_order_status_negative_case":
        intent_not_order_status = None
        if isinstance(intent_after, str):
            intent_not_order_status = intent_after not in ORDER_STATUS_INTENTS
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
    elif scenario.scenario_key == "followup_after_autoclose":
        add_check(
            "followup_reply_sent",
            followup_reply_sent is False if followup_reply_sent is not None else None,
            True,
            "No auto-reply sent after follow-up.",
        )
        add_check(
            "followup_routed_support",
            followup_routed_support is True
            if followup_routed_support is not None
            else None,
            True,
            "Follow-up routed to human support.",
        )
        add_check(
            "outbound_attempted",
            outbound_attempted is True if outbound_attempted is not None else None,
            True,
            "Initial outbound reply attempt observed.",
        )
        add_check(
            "send_message_path_confirmed",
            send_message_path_confirmed is True
            if send_message_path_confirmed is not None
            else None,
            True,
            "Initial send-message path confirmed.",
        )
        add_check(
            "operator_reply_confirmed",
            operator_reply_confirmed is True
            if operator_reply_confirmed is not None
            else None,
            True,
            "Initial operator reply confirmed.",
        )
        add_check(
            "closed_after",
            closed_after is True if closed_after is not None else None,
            True,
            "Ticket closed/resolved after reply.",
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
        "scenario": scenario.scenario_key,
        "order_number_fingerprint": scenario.order_number_fingerprint,
        "status": status,
        "failure_reason": failure_reason,
        "checks": checks,
    }
    return status, failure_reason


def _run_scenario(
    args: argparse.Namespace,
    *,
    scenario: ScenarioSpec,
    run_id: str,
    artifacts_dir: Path,
) -> ScenarioRunResult:
    proof_path = artifacts_dir / "PROOF" / scenario.proof_filename
    created_ticket_path = (
        artifacts_dir / "PROOF" / f"created_ticket_{scenario.scenario_key}.json"
    )
    commands: List[List[str]] = []
    proof: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    ticket_number = args.ticket_number
    ticket_id = args.ticket_id
    if args.suite and (ticket_number or ticket_id):
        return ScenarioRunResult(
            scenario_key=scenario.scenario_key,
            proof_path=proof_path,
            status="ERROR",
            error="ticket-number/ticket-id not supported with --suite",
            proof=None,
            commands=[],
        )

    try:
        explicit_ticket = bool(ticket_number or ticket_id)
        if not explicit_ticket:
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
            commands.append(create_cmd)
            create_result = _run_command(create_cmd)
            if create_result.returncode == 0:
                ref = _extract_ticket_ref(create_result.stdout)
                ticket_number = ref.get("ticket_number") or None
                ticket_id = ref.get("ticket_id") or None
            if not ticket_number and not ticket_id:
                raise RuntimeError("Ticket creation failed; no ticket ref available.")

        smoke_cmd = _build_smoke_cmd(
            args,
            scenario=scenario,
            proof_path=proof_path,
            run_id=run_id,
            ticket_number=ticket_number,
            ticket_id=ticket_id,
        )
        commands.append(smoke_cmd)
        smoke_result = _run_command(smoke_cmd)
        if smoke_result.returncode != 0:
            raise RuntimeError(f"dev_e2e_smoke.py failed (exit={smoke_result.returncode}).")
    except Exception as exc:
        error = str(exc)
    finally:
        proof = _read_proof(proof_path)
        assertion_status = None
        assertion_reason = None
        if proof and isinstance(proof, dict):
            assertion_status, assertion_reason = _append_scenario_assertions(
                proof,
                scenario=scenario,
            )
            proof_path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
        if assertion_status == "FAIL" and not error:
            error = assertion_reason or "Scenario assertions failed."

    status = "PASS" if not error else "FAIL"
    return ScenarioRunResult(
        scenario_key=scenario.scenario_key,
        proof_path=proof_path,
        status=status,
        error=error,
        proof=proof,
        commands=commands,
    )


def _suite_summary_md(results: List[ScenarioRunResult], *, run_id: str) -> str:
    lines = [
        "# Sandbox E2E Suite Summary — B67/A",
        "",
        f"- Timestamp: `{_iso_timestamp()}`",
        f"- Run ID: `{run_id}`",
        "",
        "## Scenario results",
    ]
    for result in results:
        status = result.status
        error = result.error or "none"
        lines.append(
            f"- `{result.scenario_key}`: `{status}` "
            f"(proof: `{result.proof_path.name}`, error: `{error}`)"
        )
    lines.append("")
    lines.append("## Commands (redacted)")
    for result in results:
        if not result.commands:
            continue
        lines.append(f"### {result.scenario_key}")
        lines.append("```powershell")
        lines.append(f"cd {ROOT}")
        for cmd in result.commands:
            lines.append(_redact_command(cmd))
        lines.append("```")
    return "\n".join(lines) + "\n"


def _suite_results_json(
    results: List[ScenarioRunResult], *, run_id: str, env_flags: Dict[str, Optional[str]]
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "timestamp": _iso_timestamp(),
        "environment": "sandbox",
        "env_flags": env_flags,
        "scenarios": [
            {
                "scenario": result.scenario_key,
                "status": result.status,
                "error": result.error,
                "proof_path": str(result.proof_path),
            }
            for result in results
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the B67 sandbox E2E suite."
    )
    parser.add_argument(
        "--scenario",
        choices=[
            "order_status_golden",
            "order_status_fallback_email_match",
            "not_order_status_negative_case",
            "followup_after_autoclose",
        ],
        help="Single scenario to run.",
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Run the full suite (all scenarios).",
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
    parser.add_argument("--ticket-number", help="Use existing ticket number (single scenario).")
    parser.add_argument("--ticket-id", help="Use existing ticket ID (single scenario).")
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
        "--followup-message",
        default="Following up on my order status. Any update?",
        help="Custom follow-up message for follow-up scenario.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=str(DEFAULT_ARTIFACT_DIR),
        help="Directory for run artifacts.",
    )
    parser.add_argument(
        "--suite-results-path",
        default=str(DEFAULT_SUITE_RESULTS),
        help="Path to write suite results JSON.",
    )
    parser.add_argument(
        "--suite-summary-path",
        default=str(DEFAULT_SUITE_SUMMARY),
        help="Path to write suite summary Markdown.",
    )
    args = parser.parse_args()
    if not args.suite and not args.scenario:
        parser.error("Specify --suite or --scenario.")
    if args.suite and args.scenario:
        parser.error("--suite and --scenario are mutually exclusive.")
    return args


def main() -> int:
    args = parse_args()
    artifacts_dir = Path(args.artifacts_dir)
    run_id = (
        args.run_id
        or os.environ.get("RUN_ID")
        or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    )

    scenario_keys = (
        [
            "order_status_golden",
            "order_status_fallback_email_match",
            "not_order_status_negative_case",
            "followup_after_autoclose",
        ]
        if args.suite
        else [args.scenario]
    )

    results: List[ScenarioRunResult] = []
    for key in scenario_keys:
        args.scenario = key
        scenario = _build_scenario_spec(args, run_id=run_id)
        results.append(
            _run_scenario(
                args,
                scenario=scenario,
                run_id=run_id,
                artifacts_dir=artifacts_dir,
            )
        )

    env_flags = _capture_env_flags()
    suite_results = _suite_results_json(results, run_id=run_id, env_flags=env_flags)
    suite_results_path = Path(args.suite_results_path)
    suite_summary_path = Path(args.suite_summary_path)
    _ensure_parent(suite_results_path)
    _ensure_parent(suite_summary_path)
    suite_results_path.write_text(
        json.dumps(suite_results, indent=2) + "\n", encoding="utf-8"
    )
    suite_summary_path.write_text(
        _suite_summary_md(results, run_id=run_id), encoding="utf-8"
    )

    failed = [result for result in results if result.status != "PASS"]
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
