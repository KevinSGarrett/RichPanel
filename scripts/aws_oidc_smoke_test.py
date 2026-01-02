#!/usr/bin/env python3
"""
aws_oidc_smoke_test.py

Lightweight smoke test run under the deploy role to ensure:
- OIDC credentials resolve to the expected AWS account.
- Kill switch parameters in SSM Parameter Store are readable.
- Secrets Manager entries that deploys rely on exist (metadata only).

Design constraints:
- Standard library only (shells out to the AWS CLI).
- No secret values are printed; we only report resource names.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Sequence

SSM_PARAMETER_SUFFIXES = [
    "safe_mode",
    "automation_enabled",
]

SECRET_SUFFIXES = [
    "richpanel/api_key",
    "richpanel/webhook_token",
    "openai/api_key",
    "shipstation/api_key",
    "shipstation/api_secret",
    "shipstation/api_base",
]


class SmokeTestError(RuntimeError):
    """Raised when an AWS smoke test check fails."""


def aws_env(region: str) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("AWS_REGION", region)
    env.setdefault("AWS_DEFAULT_REGION", region)
    return env


def run_aws_command(args: Sequence[str], *, env_vars: dict[str, str], redact_output: bool) -> str:
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
        raise SmokeTestError("AWS CLI is required but was not found in PATH.") from exc

    if proc.returncode != 0:
        sys.stderr.write(f"[ERROR] AWS CLI command failed: {' '.join(cmd)}\n")
        if proc.stdout:
            sys.stderr.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        raise SmokeTestError(f"AWS CLI command failed: {' '.join(cmd)}")

    if not redact_output and proc.stdout:
        print(proc.stdout.strip())

    return proc.stdout


def check_identity(*, expected_account: str | None, env_vars: dict[str, str]) -> None:
    print("\n[1/3] Verifying caller identity via aws sts get-caller-identity")
    raw = run_aws_command(
        ["sts", "get-caller-identity", "--output", "json"],
        env_vars=env_vars,
        redact_output=True,
    )
    data = json.loads(raw)
    account = data.get("Account")
    arn = data.get("Arn")

    print(f"    Account: {account}")
    print(f"    ARN: {arn}")

    if expected_account and account != expected_account:
        raise SmokeTestError(
            f"Expected AWS account {expected_account}, but received {account}."
        )


def build_ssm_parameter_names(env_name: str) -> list[str]:
    return [f"/rp-mw/{env_name}/{suffix}" for suffix in SSM_PARAMETER_SUFFIXES]


def build_secret_names(env_name: str) -> list[str]:
    return [f"rp-mw/{env_name}/{suffix}" for suffix in SECRET_SUFFIXES]


def check_ssm_parameters(*, env_name: str, env_vars: dict[str, str]) -> None:
    print("\n[2/3] Verifying read access to SSM kill switches")
    names = build_ssm_parameter_names(env_name)
    raw = run_aws_command(
        [
            "ssm",
            "get-parameters",
            "--names",
            *names,
            "--with-decryption",
            "--output",
            "json",
        ],
        env_vars=env_vars,
        redact_output=True,
    )
    payload = json.loads(raw)
    found = {param["Name"] for param in payload.get("Parameters", [])}
    missing = [name for name in names if name not in found]

    if missing:
        raise SmokeTestError(
            f"Missing or unreadable SSM parameters: {', '.join(missing)}"
        )

    print("    OK:", ", ".join(sorted(found)))


def check_secrets(*, env_name: str, env_vars: dict[str, str]) -> None:
    print("\n[3/3] Verifying Secrets Manager namespaces (metadata only)")
    secrets = build_secret_names(env_name)
    missing: list[str] = []

    for secret in secrets:
        try:
            run_aws_command(
                [
                    "secretsmanager",
                    "describe-secret",
                    "--secret-id",
                    secret,
                    "--output",
                    "json",
                ],
                env_vars=env_vars,
                redact_output=True,
            )
            print(f"    OK: {secret}")
        except SmokeTestError:
            missing.append(secret)

    if missing:
        raise SmokeTestError(
            f"Missing Secrets Manager entries: {', '.join(missing)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify AWS deploy-role permissions for kill switches + secrets."
    )
    parser.add_argument(
        "--env",
        required=True,
        help="Environment name (e.g. dev, staging, prod).",
    )
    parser.add_argument(
        "--region",
        required=True,
        help="AWS region to target (e.g. us-east-2).",
    )
    parser.add_argument(
        "--expected-account",
        help="Optional AWS account id to enforce for the assumed role.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_vars = aws_env(args.region)

    try:
        check_identity(expected_account=args.expected_account, env_vars=env_vars)
        check_ssm_parameters(env_name=args.env, env_vars=env_vars)
        check_secrets(env_name=args.env, env_vars=env_vars)
    except SmokeTestError as err:
        print(f"\n[FAIL] AWS smoke test failed: {err}")
        return 1

    print("\n[OK] AWS smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

