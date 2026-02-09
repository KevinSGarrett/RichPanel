from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aws_account_preflight import ENV_ACCOUNT_IDS, normalize_env, resolve_region, run_account_preflight
from secrets_preflight import _build_account_fix_suggestion, _build_secret_fix_suggestion, _check_secret

try:  # pragma: no cover - exercised in integration runs
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - offline/test mode
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow tests without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


REQUIRED_SHOPIFY_SECRETS = [
    "rp-mw/{env}/shopify/admin_api_token",
    "rp-mw/{env}/shopify/client_id",
    "rp-mw/{env}/shopify/client_secret",
    "rp-mw/{env}/shopify/refresh_token",
]


def _required_secret_ids(env_name: str) -> List[str]:
    return [secret.format(env=env_name) for secret in REQUIRED_SHOPIFY_SECRETS]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _print_account_identity(account_result: Any, region: str) -> None:
    account_id = account_result.aws_account_id or "unknown"
    arn = account_result.aws_arn or "unknown"
    print(f"[AWS PREFLIGHT] account_id={account_id} arn={arn} region={region}")


def run_aws_secrets_preflight(
    *,
    env_name: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    expected_account_id: Optional[str] = None,
    require_secrets: Optional[List[str]] = None,
    session: Optional["boto3.session.Session"] = None,
    out_path: Optional[str] = None,
    fail_on_error: bool = True,
) -> Dict[str, Any]:
    normalized_env = normalize_env(env_name)
    resolved_region = resolve_region(region)
    expected_account_id = expected_account_id or ENV_ACCOUNT_IDS.get(normalized_env)

    account_result = run_account_preflight(
        env_name=normalized_env,
        region=resolved_region,
        expected_account_id=expected_account_id,
        profile=profile,
        session=session,
        fail_on_error=False,
    )

    if boto3 is None:
        payload = {
            "env": normalized_env,
            "aws_account_id": account_result.aws_account_id,
            "aws_arn": account_result.aws_arn,
            "region": resolved_region,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "account_preflight": account_result.as_dict(),
            "secrets": {},
            "overall_status": "FAIL",
            "error": "boto3_unavailable",
        }
        if out_path:
            _write_json(out_path, payload)
        if fail_on_error:
            raise SystemExit("AWS secrets preflight failed: boto3 unavailable.")
        return payload

    if not account_result.ok and fail_on_error:
        _print_account_identity(account_result, resolved_region)
        if account_result.error and account_result.error.startswith("region_mismatch"):
            raise SystemExit(
                "AWS preflight failed: wrong region "
                f"(expected {account_result.expected_region}, got {resolved_region})."
            )
        if account_result.error == "unknown_env":
            raise SystemExit(
                f"AWS preflight failed: unknown env '{normalized_env}'."
            )
        suggestion = _build_account_fix_suggestion(
            expected_account_id=expected_account_id,
            actual_account_id=account_result.aws_account_id,
            region=resolved_region,
        )
        raise SystemExit(
            "AWS preflight failed: wrong account "
            f"(expected {expected_account_id}, got {account_result.aws_account_id}). "
            f"{suggestion}"
        )

    _print_account_identity(account_result, resolved_region)

    session = session or boto3.session.Session(
        profile_name=profile, region_name=resolved_region
    )
    secrets_client = session.client("secretsmanager", region_name=resolved_region)

    required = _required_secret_ids(normalized_env)
    extra_required = [item.strip() for item in (require_secrets or []) if item.strip()]
    for secret_id in extra_required:
        if secret_id not in required:
            required.append(secret_id)

    results: Dict[str, Dict[str, Any]] = {}
    for secret_id in required:
        result = _check_secret(
            secrets_client,
            secret_id,
            required=True,
        )
        results[secret_id] = result.as_dict()

    failures = [
        key
        for key, value in results.items()
        if value.get("required")
        and (not value.get("exists") or not value.get("readable"))
    ]
    overall_ok = bool(account_result.ok) and not failures

    payload = {
        "env": normalized_env,
        "aws_account_id": account_result.aws_account_id,
        "aws_arn": account_result.aws_arn,
        "region": resolved_region,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "account_preflight": account_result.as_dict(),
        "secrets": results,
        "overall_status": "PASS" if overall_ok else "FAIL",
        "failures": {
            "account": None if account_result.ok else account_result.error,
            "required_secrets": failures,
        },
    }
    if out_path:
        _write_json(out_path, payload)

    if fail_on_error and not overall_ok:
        detail_lines = [
            "AWS secrets preflight failed:",
            f"- account_id: {account_result.aws_account_id or 'unknown'}",
            f"- arn: {account_result.aws_arn or 'unknown'}",
            f"- region: {resolved_region}",
        ]
        for secret_id in failures:
            secret_result = results.get(secret_id, {})
            error_name = secret_result.get("error")
            error_message = secret_result.get("error_message")
            error_detail = (
                f"{error_name}: {error_message}"
                if error_name and error_message
                else (error_name or error_message or "unknown_error")
            )
            suggestion = _build_secret_fix_suggestion(
                expected_account_id=expected_account_id,
                actual_account_id=account_result.aws_account_id,
                region=resolved_region,
                error_name=error_name,
                error_message=error_message,
            )
            detail_lines.extend(
                [
                    f"- secret_id: {secret_id}",
                    f"- error: {error_detail}",
                    f"- suggested_fix: {suggestion}",
                ]
            )
        raise SystemExit("\n".join(detail_lines))

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PII-safe preflight for Shopify secrets in AWS Secrets Manager."
    )
    parser.add_argument("--env", required=True, help="Target environment (dev|staging|prod).")
    parser.add_argument("--region", help="AWS region override (default: env/AWS default).")
    parser.add_argument(
        "--profile",
        "--aws-profile",
        dest="profile",
        help="AWS profile to use for the preflight session.",
    )
    parser.add_argument(
        "--expect-account-id",
        dest="expect_account_id",
        help="Expected AWS account id for the run.",
    )
    parser.add_argument(
        "--require-secret",
        action="append",
        default=[],
        help="Require a Secrets Manager secret id (repeatable).",
    )
    parser.add_argument(
        "--out",
        "--out-json",
        dest="out",
        help="Optional JSON output path.",
    )
    args = parser.parse_args()

    payload = run_aws_secrets_preflight(
        env_name=args.env,
        region=args.region,
        profile=args.profile,
        expected_account_id=args.expect_account_id,
        require_secrets=args.require_secret,
        out_path=args.out,
        fail_on_error=False,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("overall_status") == "PASS" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
