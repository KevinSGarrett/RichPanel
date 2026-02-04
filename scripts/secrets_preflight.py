from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aws_account_preflight import run_account_preflight, resolve_region

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
        if self.source:
            payload["source"] = self.source
        if self.note:
            payload["note"] = self.note
        return payload


def _normalize_env(env_name: str) -> str:
    normalized = (env_name or "").strip().lower()
    if normalized == "production":
        return "prod"
    return normalized or "local"


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
            note=note,
        )
    return CheckResult(exists=True, readable=True, required=required, note=note)


def run_secrets_preflight(
    *,
    env_name: str,
    region: Optional[str] = None,
    session: Optional["boto3.session.Session"] = None,
    out_path: Optional[str] = None,
    fail_on_error: bool = True,
) -> Dict[str, Any]:
    normalized_env = _normalize_env(env_name)
    resolved_region = resolve_region(region)

    account_result = run_account_preflight(
        env_name=normalized_env,
        region=resolved_region,
        session=session,
        fail_on_error=False,
    )

    if boto3 is None:
        payload = {
            "env": normalized_env,
            "aws_account_id": account_result.aws_account_id,
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

    session = session or boto3.session.Session(region_name=resolved_region)
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
        raise SystemExit(
            "Secrets preflight failed: "
            f"account_ok={account_ok} "
            f"required_secrets_missing={len(required_secret_failures)} "
            f"required_ssm_missing={len(required_ssm_failures)}."
        )
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
    parser.add_argument("--out", help="Optional JSON output path.")
    args = parser.parse_args()

    payload = run_secrets_preflight(
        env_name=args.env,
        region=args.region,
        out_path=args.out,
        fail_on_error=False,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("overall_status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
