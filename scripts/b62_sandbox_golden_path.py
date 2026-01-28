#!/usr/bin/env python3
"""
b62_sandbox_golden_path.py

One-command Golden Path proof harness for sandbox/dev.
Creates a sandbox ticket, runs dev_e2e_smoke.py, and writes PII-safe artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
DEFAULT_ARTIFACT_DIR = ROOT / "REHYDRATION_PACK" / "RUNS" / "B62" / "A"
DEFAULT_PROOF_PATH = (
    DEFAULT_ARTIFACT_DIR / "PROOF" / "sandbox_golden_path_proof.json"
)

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
}


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


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
                    "ticket_number_fingerprint": payload.get("ticket_number_fingerprint"),
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


def _git_diffstat(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--stat"],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return "(git not available)"
    if result.returncode != 0:
        return f"(git diff failed: {result.stderr.strip() or 'unknown error'})"
    return result.stdout.strip() or "(no changes)"


def _proof_excerpt(proof: Optional[Dict[str, Any]]) -> str:
    if not proof:
        return json.dumps({"error": "proof not available"}, indent=2)
    fields = proof.get("proof_fields", {}) if isinstance(proof, dict) else {}
    excerpt = {
        "openai_routing_used": fields.get("openai_routing_used"),
        "openai_rewrite_used": fields.get("openai_rewrite_used"),
        "outbound_send_message_status": fields.get("outbound_send_message_status"),
        "send_message_path_confirmed": fields.get("send_message_path_confirmed"),
        "send_message_tag_present": fields.get("send_message_tag_present"),
        "latest_comment_is_operator": fields.get("latest_comment_is_operator"),
        "closed_after": fields.get("closed_after"),
        "followup_reply_sent": fields.get("followup_reply_sent"),
        "followup_routed_support": fields.get("followup_routed_support"),
    }
    return json.dumps(excerpt, indent=2)


def _write_run_report(
    path: Path,
    *,
    proof: Optional[Dict[str, Any]],
    error: Optional[str],
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
        "# Run Report — B62/A",
        "",
        f"- Timestamp: `{_iso_timestamp()}`",
        f"- Status: `{status or 'UNKNOWN'}`",
        f"- Classification: `{classification or 'unknown'}`",
        f"- Failure reason: `{failure_reason or classification_reason or 'none'}`",
        f"- Ticket fingerprint: `{ticket_fingerprint or 'n/a'}`",
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
        "# Evidence — B62/A",
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
        lines.extend(
            [
                "",
                "## Internal command — create ticket",
            ]
        )
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
        lines.extend(
            [
                "",
                "## Internal command — find recent ticket",
            ]
        )
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
        lines.extend(
            [
                "",
                "## Internal command — smoke proof",
            ]
        )
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
        "# Changes — B62/A",
        "",
        "## Intent",
        "- Add B62 sandbox golden path wrapper and proof-field strengthening.",
        "- Add unit tests for outbound classification and reply content flags.",
        "",
        "## Diffstat",
        "```",
        diffstat or "(no changes)",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the B62 sandbox golden path harness."
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
        "--artifacts-dir",
        default=str(DEFAULT_ARTIFACT_DIR),
        help="Directory for run artifacts.",
    )
    parser.add_argument(
        "--proof-path",
        default=str(DEFAULT_PROOF_PATH),
        help="Path to write proof JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts_dir = Path(args.artifacts_dir)
    proof_path = Path(args.proof_path)
    created_ticket_path = artifacts_dir / "PROOF" / "created_ticket.json"
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
                "order_status",
                "--require-openai-routing",
                "--require-openai-rewrite",
                "--require-outbound",
                "--require-send-message",
                "--require-operator-reply",
                "--followup",
                "--proof-path",
                str(proof_path),
            ]
            if args.profile:
                smoke_cmd.extend(["--profile", args.profile])
            if args.run_id:
                smoke_cmd.extend(["--run-id", args.run_id])
            if ticket_number:
                smoke_cmd.extend(["--ticket-number", ticket_number])
            elif ticket_id:
                smoke_cmd.extend(["--ticket-id", ticket_id])
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
        _write_run_report(run_report_path, proof=proof, error=error)
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
