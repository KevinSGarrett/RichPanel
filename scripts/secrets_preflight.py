from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aws_account_preflight import (
    ENV_ACCOUNT_IDS,
    normalize_env,
    run_account_preflight,
    resolve_region,
)

try:  # pragma: no cover - exercised in integration runs
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - offline/test mode
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow tests without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


DEFAULT_REQUIRED_SECRETS = [
    {
        "label": "openai_api_key",
        "secret_id": "rp-mw/{env}/openai/api_key",
        "required": True,
    },
    {
        "label": "richpanel_api_key",
        "secret_id": "rp-mw/{env}/richpanel/api_key",
        "required": True,
    },
    {
        "label": "richpanel_webhook_token",
        "secret_id": "rp-mw/{env}/richpanel/webhook_token",
        "required": True,
    },
    {
        "label": "shopify_admin_api_token",
        "secret_id": "rp-mw/{env}/shopify/admin_api_token",
        "required": True,
    },
    {
        "label": "shopify_access_token_legacy",
        "secret_id": "rp-mw/{env}/shopify/access_token",
        "required": False,
        "note": "Legacy fallback for Shopify client.",
    },
    {
        "label": "shopify_client_id",
        "secret_id": "rp-mw/{env}/shopify/client_id",
        "required": False,
    },
    {
        "label": "shopify_client_secret",
        "secret_id": "rp-mw/{env}/shopify/client_secret",
        "required": False,
    },
    {
        "label": "richpanel_bot_agent_id",
        "secret_id": "rp-mw/{env}/richpanel/bot_agent_id",
        "required": True,
        "note": "Can be provided via RICHPANEL_BOT_AGENT_ID env var instead.",
    },
]

DEFAULT_SSM_PARAMS = [
    {
        "label": "safe_mode",
        "name": "/rp-mw/{env}/safe_mode",
        "required": True,
    },
    {
        "label": "automation_enabled",
        "name": "/rp-mw/{env}/automation_enabled",
        "required": True,
    },
]


@dataclass(frozen=True)
class CheckResult:
    exists: bool
    readable: bool
    required: bool
    error: Optional[str] = None
    error_message: Optional[str] = None
    source: Optional[str] = None
    note: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "exists": self.exists,
            "readable": self.readable,
            "required": self.required,
        }
        if self.error:
            payload["error"] = self.error
        if self.error_message:
            payload["error_message"] = self.error_message
        if self.source:
            payload["source"] = self.source
        if self.note:
            payload["note"] = self.note
        return payload


def _check_secret(
    secrets_client: Any,
    secret_id: str,
    *,
    required: bool,
    note: Optional[str] = None,
) -> CheckResult:
    try:
        secrets_client.describe_secret(SecretId=secret_id)
    except (BotoCoreError, ClientError, Exception) as exc:
        error_name = exc.__class__.__name__
        return CheckResult(
            exists=False,
            readable=False,
            required=required,
            error=error_name,
            error_message=str(exc) or None,
            note=note,
        )
    try:
        secrets_client.get_secret_value(SecretId=secret_id)
    except (BotoCoreError, ClientError, Exception) as exc:
        return CheckResult(
            exists=True,
            readable=False,
            required=required,
            error=exc.__class__.__name__,
            error_message=str(exc) or None,
            note=note,
        )
    return CheckResult(
        exists=True,
        readable=True,
        required=required,
        note=note,
    )


def _check_ssm_param(
    ssm_client: Any,
    name: str,
    *,
    required: bool,
    note: Optional[str] = None,
) -> CheckResult:
    try:
        response = ssm_client.describe_parameters(
            ParameterFilters=[{"Key": "Name", "Option": "Equals", "Values": [name]}]
        )
    except (BotoCoreError, ClientError, Exception) as exc:
        return CheckResult(
            exists=False,
            readable=False,
            required=required,
            error=exc.__class__.__name__,
            error_message=str(exc) or None,
            note=note,
        )
    params = response.get("Parameters") or []
    if not params:
        return CheckResult(
            exists=False,
            readable=False,
            required=required,
            error="NotFound",
            note=note,
        )
    try:
        ssm_client.get_parameter(Name=name, WithDecryption=False)
    except (BotoCoreError, ClientError, Exception) as exc:
        return CheckResult(
            exists=True,
            readable=False,
            required=required,
            error=exc.__class__.__name__,
            error_message=str(exc) or None,
            note=note,
        )
    return CheckResult(exists=True, readable=True, required=required, note=note)


def _print_account_identity(account_result: Any, region: str) -> None:
    account_id = account_result.aws_account_id or "unknown"
    arn = account_result.aws_arn or "unknown"
    print(f"[AWS PREFLIGHT] account_id={account_id} arn={arn} region={region}")


def _build_account_fix_suggestion(
    *,
    expected_account_id: Optional[str],
    actual_account_id: Optional[str],
    region: str,
) -> str:
    env_hint = {account_id: env for env, account_id in ENV_ACCOUNT_IDS.items()}
    expected_env = env_hint.get(expected_account_id or "")
    actual_env = env_hint.get(actual_account_id or "")
    hint_parts = []
    if expected_env:
        hint_parts.append(f"expected_env={expected_env}")
    if actual_env:
        hint_parts.append(f"actual_env={actual_env}")
    hint = f" ({', '.join(hint_parts)})" if hint_parts else ""
    profile_hint = (
        f" (e.g., AWS_PROFILE=rp-admin-{expected_env})" if expected_env else ""
    )
    return (
        "Re-run with the correct AWS profile/role for the intended account"
        f"{profile_hint} in region {region}.{hint}"
    )


def _build_secret_fix_suggestion(
    *,
    expected_account_id: Optional[str],
    actual_account_id: Optional[str],
    region: str,
    error_name: Optional[str],
    error_message: Optional[str],
) -> str:
    if expected_account_id and actual_account_id and expected_account_id != actual_account_id:
        return _build_account_fix_suggestion(
            expected_account_id=expected_account_id,
            actual_account_id=actual_account_id,
            region=region,
        )
    error_text = (error_name or "") + " " + (error_message or "")
    if "AccessDenied" in error_text:
        return (
            "Ensure your IAM role has secretsmanager:DescribeSecret and "
            f"secretsmanager:GetSecretValue for this secret in {region}."
        )
    if "NotFound" in error_text or "ResourceNotFound" in error_text:
        return (
            "Confirm the secret name and region. Secrets are account-specific and "
            "not shared across DEV/PROD."
        )
    return (
        "Verify AWS_PROFILE/role, region, and that the secret exists and is readable."
    )


def run_secrets_preflight(
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
            "ssm": {},
            "overall_status": "FAIL",
            "error": "boto3_unavailable",
        }
        if out_path:
            _write_json(out_path, payload)
        if fail_on_error:
            raise SystemExit("Secrets preflight failed: boto3 unavailable.")
        return payload

    if not account_result.ok and fail_on_error:
        _print_account_identity(account_result, resolved_region)
        expected_id = account_result.expected_account_id or expected_account_id
        if account_result.error and account_result.error.startswith("region_mismatch"):
            raise SystemExit(
                "AWS preflight failed: wrong region "
                f"(expected {account_result.expected_region}, got {resolved_region})."
            )
        if account_result.error == "unknown_env":
            raise SystemExit(
                f"AWS preflight failed: unknown env '{normalized_env}'."
            )
        if account_result.error == "boto3_unavailable":
            raise SystemExit("AWS preflight failed: boto3 unavailable.")
        suggestion = _build_account_fix_suggestion(
            expected_account_id=expected_id,
            actual_account_id=account_result.aws_account_id,
            region=resolved_region,
        )
        raise SystemExit(
            "AWS preflight failed: wrong account "
            f"(expected {expected_id}, got {account_result.aws_account_id}). "
            f"{suggestion}"
        )

    _print_account_identity(account_result, resolved_region)

    session = session or boto3.session.Session(
        profile_name=profile, region_name=resolved_region
    )
    secrets_client = session.client("secretsmanager", region_name=resolved_region)
    ssm_client = session.client("ssm", region_name=resolved_region)

    secrets_results: Dict[str, Dict[str, Any]] = {}
    for entry in DEFAULT_REQUIRED_SECRETS:
        secret_id = entry["secret_id"].format(env=normalized_env)
        label = entry["label"]
        note = entry.get("note")
        if label == "richpanel_bot_agent_id":
            env_override = os.environ.get("RICHPANEL_BOT_AGENT_ID")
            if env_override and env_override.strip():
                secrets_results[secret_id] = CheckResult(
                    exists=True,
                    readable=True,
                    required=bool(entry.get("required")),
                    source="env:RICHPANEL_BOT_AGENT_ID",
                    note=note,
                ).as_dict()
                continue
        result = _check_secret(
            secrets_client,
            secret_id,
            required=bool(entry.get("required")),
            note=note,
        )
        secrets_results[secret_id] = result.as_dict()

    extra_required = [item.strip() for item in (require_secrets or []) if item.strip()]
    for secret_id in extra_required:
        if secret_id in secrets_results:
            secrets_results[secret_id]["required"] = True
            continue
        result = _check_secret(secrets_client, secret_id, required=True)
        secrets_results[secret_id] = result.as_dict()

    ssm_results: Dict[str, Dict[str, Any]] = {}
    for entry in DEFAULT_SSM_PARAMS:
        name = entry["name"].format(env=normalized_env)
        result = _check_ssm_param(
            ssm_client, name, required=bool(entry.get("required")), note=entry.get("note")
        )
        ssm_results[name] = result.as_dict()

    required_secret_failures = [
        key
        for key, value in secrets_results.items()
        if value.get("required")
        and (not value.get("exists") or not value.get("readable"))
    ]
    required_ssm_failures = [
        key
        for key, value in ssm_results.items()
        if value.get("required")
        and (not value.get("exists") or not value.get("readable"))
    ]
    account_ok = bool(account_result.ok)
    overall_ok = account_ok and not required_secret_failures and not required_ssm_failures

    payload = {
        "env": normalized_env,
        "aws_account_id": account_result.aws_account_id,
        "aws_arn": account_result.aws_arn,
        "region": resolved_region,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "account_preflight": account_result.as_dict(),
        "secrets": secrets_results,
        "ssm": ssm_results,
        "overall_status": "PASS" if overall_ok else "FAIL",
        "failures": {
            "account": None if account_ok else account_result.error,
            "required_secrets": required_secret_failures,
            "required_ssm": required_ssm_failures,
        },
    }
    if out_path:
        _write_json(out_path, payload)
    if fail_on_error and not overall_ok:
        detail_lines = [
            "Secrets preflight failed:",
            f"- account_id: {account_result.aws_account_id or 'unknown'}",
            f"- arn: {account_result.aws_arn or 'unknown'}",
            f"- region: {resolved_region}",
        ]
        for secret_id in required_secret_failures:
            secret_result = secrets_results.get(secret_id, {})
            error_name = secret_result.get("error")
            error_message = secret_result.get("error_message")
            error_detail = (
                f"{error_name}: {error_message}"
                if error_name and error_message
                else (error_name or error_message or "unknown_error")
            )
            suggestion = _build_secret_fix_suggestion(
                expected_account_id=account_result.expected_account_id or expected_account_id,
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
        for param_name in required_ssm_failures:
            detail_lines.extend(
                [
                    f"- ssm_param: {param_name}",
                    "- error: Missing or unreadable required SSM parameter",
                    (
                        "- suggested_fix: Verify the SSM parameter exists in the "
                        f"{resolved_region} account and your role can read it."
                    ),
                ]
            )
        raise SystemExit("\n".join(detail_lines))
    return payload


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PII-safe preflight for Secrets Manager + SSM parameters."
    )
    parser.add_argument("--env", required=True, help="Target environment (dev|staging|prod).")
    parser.add_argument("--region", help="AWS region override (default: env/AWS default).")
    parser.add_argument("--profile", help="AWS profile to use for the preflight session.")
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
    parser.add_argument("--out", help="Optional JSON output path.")
    args = parser.parse_args()

    payload = run_secrets_preflight(
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


if __name__ == "__main__":
    raise SystemExit(main())
