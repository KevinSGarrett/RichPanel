#!/usr/bin/env python3
"""
Shared helpers for sandbox scenario wrappers.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
