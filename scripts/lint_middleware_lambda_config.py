#!/usr/bin/env python3
"""
lint_middleware_lambda_config.py

PII-safe lint for deployed Richpanel middleware Lambda configuration.
Outputs booleans and counts only; never prints secret values.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Dict, Iterable, Optional


ACK_PHRASE = "I_UNDERSTAND_PROD_WRITES"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a PII-safe summary of deployed middleware Lambda env vars "
            "(booleans and counts only)."
        )
    )
    parser.add_argument(
        "--env", default="dev", help="Environment name (default: dev)."
    )
    parser.add_argument(
        "--region", default="us-east-2", help="AWS region (default: us-east-2)."
    )
    parser.add_argument(
        "--profile",
        help="Optional AWS profile name for the AWS CLI session.",
    )
    return parser.parse_args()


def aws_env(region: str, profile: Optional[str]) -> Dict[str, str]:
    env = os.environ.copy()
    env.setdefault("AWS_REGION", region)
    env.setdefault("AWS_DEFAULT_REGION", region)
    if profile:
        env["AWS_PROFILE"] = profile
    return env


def run_aws_command(args: Iterable[str], *, env_vars: Dict[str, str]) -> str:
    cmd = ["aws", *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env_vars,
            check=False,
        )
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("AWS CLI is required but was not found in PATH.") from exc

    if proc.returncode != 0:
        raise RuntimeError(
            "AWS CLI command failed. Re-run with valid credentials and region."
        )

    return proc.stdout


def _to_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _acknowledged(value: Optional[str]) -> bool:
    if value is None:
        return False
    if _to_bool(value):
        return True
    return str(value).strip().upper() == ACK_PHRASE


def _parse_allowlist(value: Optional[str], *, strip_at: bool) -> set[str]:
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


def _safe_len(value: Optional[str]) -> int:
    if value is None:
        return 0
    return 1 if str(value).strip() else 0


def main() -> int:
    args = parse_args()
    env_name = str(args.env).strip()
    if not env_name:
        print("[FAIL] --env must be a non-empty string.", file=sys.stderr)
        return 2

    function_name = f"rp-mw-{env_name}-worker"
    env_vars = aws_env(args.region, args.profile)

    try:
        raw = run_aws_command(
            [
                "lambda",
                "get-function-configuration",
                "--function-name",
                function_name,
                "--output",
                "json",
                "--region",
                args.region,
            ],
            env_vars=env_vars,
        )
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("[FAIL] Unable to parse AWS CLI output as JSON.", file=sys.stderr)
        return 1

    variables = payload.get("Environment", {}).get("Variables", {}) or {}
    outbound_enabled = _to_bool(variables.get("RICHPANEL_OUTBOUND_ENABLED"))
    ack_ok = _acknowledged(variables.get("MW_PROD_WRITES_ACK"))
    allowlist_emails = _parse_allowlist(
        variables.get("MW_OUTBOUND_ALLOWLIST_EMAILS"), strip_at=False
    )
    allowlist_domains = _parse_allowlist(
        variables.get("MW_OUTBOUND_ALLOWLIST_DOMAINS"), strip_at=True
    )
    bot_agent_present = _safe_len(variables.get("RICHPANEL_BOT_AGENT_ID")) > 0
    bot_author_present = _safe_len(variables.get("RICHPANEL_BOT_AUTHOR_ID")) > 0

    print(f"Environment: {env_name}")
    print(f"Function: {function_name}")
    print(f"Outbound enabled: {str(outbound_enabled).lower()}")
    print(f"Prod writes ACK acknowledged: {str(ack_ok).lower()}")
    print(f"Allowlist emails: {len(allowlist_emails)}")
    print(f"Allowlist domains: {len(allowlist_domains)}")
    print(f"Bot agent id set: {str(bot_agent_present).lower()}")
    print(f"Bot author id set: {str(bot_author_present).lower()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
