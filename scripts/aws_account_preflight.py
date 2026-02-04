from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

try:  # pragma: no cover - exercised in integration runs
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - offline/test mode
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow tests without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


DEFAULT_REGION = "us-east-2"
ENV_ACCOUNT_IDS: Dict[str, str] = {
    "dev": "151124909266",
    "staging": "260475105304",
    "prod": "878145708918",
}
ENV_REGIONS: Dict[str, str] = {
    "dev": "us-east-2",
    "staging": "us-east-2",
    "prod": "us-east-2",
}


@dataclass(frozen=True)
class AccountPreflightResult:
    env: str
    region: str
    aws_account_id: Optional[str]
    expected_account_id: Optional[str]
    expected_region: Optional[str]
    ok: bool
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "env": self.env,
            "region": self.region,
            "aws_account_id": self.aws_account_id,
            "expected_account_id": self.expected_account_id,
            "expected_region": self.expected_region,
            "ok": self.ok,
            "error": self.error,
        }


def _normalize_env(env_name: str) -> str:
    normalized = (env_name or "").strip().lower()
    if normalized == "production":
        return "prod"
    return normalized or "local"


def resolve_region(region: Optional[str]) -> str:
    if region:
        return str(region).strip()
    return (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or DEFAULT_REGION
    )


def run_account_preflight(
    *,
    env_name: str,
    region: Optional[str] = None,
    session: Optional["boto3.session.Session"] = None,
    fail_on_error: bool = True,
) -> AccountPreflightResult:
    normalized_env = _normalize_env(env_name)
    resolved_region = resolve_region(region)
    expected_account = ENV_ACCOUNT_IDS.get(normalized_env)
    expected_region = ENV_REGIONS.get(normalized_env)

    if boto3 is None:
        result = AccountPreflightResult(
            env=normalized_env,
            region=resolved_region,
            aws_account_id=None,
            expected_account_id=expected_account,
            expected_region=expected_region,
            ok=False,
            error="boto3_unavailable",
        )
        if fail_on_error:
            raise SystemExit("AWS account preflight failed: boto3 unavailable.")
        return result

    if normalized_env not in ENV_ACCOUNT_IDS:
        result = AccountPreflightResult(
            env=normalized_env,
            region=resolved_region,
            aws_account_id=None,
            expected_account_id=expected_account,
            expected_region=expected_region,
            ok=False,
            error="unknown_env",
        )
        if fail_on_error:
            raise SystemExit(
                f"AWS account preflight failed: unknown env '{normalized_env}'."
            )
        return result

    if expected_region and resolved_region != expected_region:
        result = AccountPreflightResult(
            env=normalized_env,
            region=resolved_region,
            aws_account_id=None,
            expected_account_id=expected_account,
            expected_region=expected_region,
            ok=False,
            error=f"region_mismatch(expected={expected_region},actual={resolved_region})",
        )
        if fail_on_error:
            raise SystemExit(
                "AWS account preflight failed: wrong region "
                f"(expected {expected_region}, got {resolved_region})."
            )
        return result

    session = session or boto3.session.Session(region_name=resolved_region)
    sts_client = session.client("sts", region_name=resolved_region)
    try:
        identity = sts_client.get_caller_identity()
    except (BotoCoreError, ClientError, Exception) as exc:
        result = AccountPreflightResult(
            env=normalized_env,
            region=resolved_region,
            aws_account_id=None,
            expected_account_id=expected_account,
            expected_region=expected_region,
            ok=False,
            error=exc.__class__.__name__,
        )
        if fail_on_error:
            raise SystemExit(
                f"AWS account preflight failed: {exc.__class__.__name__}."
            )
        return result

    actual_account = identity.get("Account")
    ok = actual_account == expected_account
    result = AccountPreflightResult(
        env=normalized_env,
        region=resolved_region,
        aws_account_id=actual_account,
        expected_account_id=expected_account,
        expected_region=expected_region,
        ok=ok,
        error=None if ok else "account_mismatch",
    )
    if not ok and fail_on_error:
        raise SystemExit(
            "AWS account preflight failed: wrong account "
            f"(expected {expected_account}, got {actual_account})."
        )
    return result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Preflight check to verify AWS account + region for an env."
    )
    parser.add_argument("--env", required=True, help="Target environment (dev|staging|prod).")
    parser.add_argument("--region", help="AWS region override (default: env/AWS default).")
    args = parser.parse_args()

    result = run_account_preflight(env_name=args.env, region=args.region, fail_on_error=False)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
