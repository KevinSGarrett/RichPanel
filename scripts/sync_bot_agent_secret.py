from __future__ import annotations

import argparse
from typing import Optional

from aws_account_preflight import normalize_env, resolve_region

try:  # pragma: no cover - exercised in integration runs
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - offline/test mode
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow tests without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


def _fetch_bot_agent_id(lambda_client, *, env_name: str) -> str:
    function_name = f"rp-mw-{env_name}-worker"
    config = lambda_client.get_function_configuration(FunctionName=function_name)
    variables = (config.get("Environment") or {}).get("Variables") or {}
    candidate = variables.get("RICHPANEL_BOT_AGENT_ID") or ""
    if str(candidate).strip():
        return str(candidate).strip()
    raise SystemExit(
        f"RICHPANEL_BOT_AGENT_ID not set on {function_name}; "
        "cannot sync bot agent secret."
    )


def _secret_exists(secrets_client, *, secret_id: str) -> bool:
    try:
        secrets_client.describe_secret(SecretId=secret_id)
    except (BotoCoreError, ClientError, Exception):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync RICHPANEL_BOT_AGENT_ID from Lambda env into Secrets Manager."
    )
    parser.add_argument("--env", required=True, help="Target environment (dev|staging|prod).")
    parser.add_argument("--region", help="AWS region override (default: us-east-2).")
    args = parser.parse_args()
    return main_with_args(env=args.env, region=args.region)


def main_with_args(*, env: str, region: Optional[str] = None) -> int:
    if boto3 is None:
        raise SystemExit("boto3 is required to sync bot agent secrets.")

    env_name = normalize_env(env)
    resolved_region = resolve_region(region)
    session = boto3.session.Session(region_name=resolved_region)
    lambda_client = session.client("lambda", region_name=resolved_region)
    secrets_client = session.client("secretsmanager", region_name=resolved_region)
    secret_id = f"rp-mw/{env_name}/richpanel/bot_agent_id"

    if _secret_exists(secrets_client, secret_id=secret_id):
        print(f"[OK] Secret already exists: {secret_id}")
        return 0

    bot_agent_id = _fetch_bot_agent_id(lambda_client, env_name=env_name)
    secrets_client.create_secret(Name=secret_id, SecretString=bot_agent_id)
    print(f"[OK] Secret created: {secret_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
