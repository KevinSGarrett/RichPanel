from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from integrations.common import resolve_env_name  # noqa: E402
from integrations.shopify.client import (  # noqa: E402
    ShopifyClient,
    ShopifyRequestError,
    TransportError as ShopifyTransportError,
    TransportRequest as ShopifyTransportRequest,
)
from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelClient,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)

try:  # pragma: no cover - exercised in integration runs
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - offline/test mode
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow tests without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


REQUIRED_FLAG_VALUES: Dict[str, str] = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_READ_ONLY": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
    "RICHPANEL_OUTBOUND_ENABLED": "false",
    "SHOPIFY_OUTBOUND_ENABLED": "true",
    "SHOPIFY_WRITE_DISABLED": "true",
}

REQUIRED_ENV_VARS = [
    "SHOPIFY_SHOP_DOMAIN",
]

REQUIRED_SECRET_SUFFIXES = [
    ("richpanel", "api_key"),
    ("shopify", "admin_api_token"),
    ("shopify", "client_id"),
    ("shopify", "client_secret"),
    ("openai", "api_key"),
]


def _write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Order status preflight health check",
        "",
        f"- timestamp_utc: {payload.get('timestamp_utc')}",
        f"- overall_status: {payload.get('overall_status')}",
        "",
        "## Checks",
    ]
    for entry in payload.get("checks", []):
        lines.append(
            f"- {entry.get('name')}: {entry.get('status')} — {entry.get('details')}"
        )
        if entry.get("next_action"):
            lines.append(f"  - next_action: {entry.get('next_action')}")
    diagnostics = payload.get("shopify_token_diagnostics")
    if diagnostics:
        lines.extend(
            [
                "",
                "## Shopify token diagnostics",
                "```",
                json.dumps(diagnostics, indent=2, sort_keys=True),
                "```",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _canonical_env(env_name: str) -> str:
    normalized = (env_name or "").strip().lower()
    if normalized == "production":
        return "prod"
    return normalized or "local"


def _check_required_env() -> Dict[str, str]:
    env_name, env_source = resolve_env_name()
    missing: List[str] = []
    mismatched: List[str] = []
    for key in REQUIRED_ENV_VARS:
        if not os.environ.get(key):
            missing.append(key)
    for key, expected in REQUIRED_FLAG_VALUES.items():
        value = os.environ.get(key)
        if value is None:
            missing.append(key)
            continue
        if str(value).strip().lower() != expected:
            mismatched.append(f"{key}={value}")
    if env_name == "local":
        mismatched.append("environment=local")
    if missing or mismatched:
        details = []
        if missing:
            details.append(f"missing={','.join(sorted(set(missing)))}")
        if mismatched:
            details.append(f"mismatched={','.join(sorted(set(mismatched)))}")
        return {
            "status": "FAIL",
            "details": "; ".join(details),
            "next_action": "Set required env vars and safety flags for read-only preflight.",
        }
    return {
        "status": "PASS",
        "details": f"env={env_name} source={env_source or 'unset'}",
    }


def _build_secret_ids(env_name: str) -> List[str]:
    canonical_env = _canonical_env(env_name)
    base = f"rp-mw/{canonical_env}"
    return [f"{base}/{group}/{name}" for group, name in REQUIRED_SECRET_SUFFIXES]


def _check_secrets(*, env_name: str) -> Dict[str, str]:
    if boto3 is None:
        return {
            "status": "FAIL",
            "details": "boto3_unavailable",
            "next_action": "Install boto3 or run in CI with AWS creds to verify secrets.",
        }
    secrets_client = boto3.client("secretsmanager")
    secret_ids = _build_secret_ids(env_name)
    failures: List[str] = []
    for secret_id in secret_ids:
        try:
            secrets_client.get_secret_value(SecretId=secret_id)
        except (BotoCoreError, ClientError, Exception) as exc:
            failures.append(f"{secret_id}({exc.__class__.__name__})")
    if failures:
        return {
            "status": "FAIL",
            "details": f"missing_or_undecodable={','.join(failures)}",
            "next_action": "Ensure required Secrets Manager entries exist and decrypt.",
        }
    return {"status": "PASS", "details": f"checked={len(secret_ids)}"}


def _check_shopify_graphql(
    *,
    shop_domain: Optional[str],
    access_token_secret_id: Optional[str],
) -> Dict[str, str]:
    client = ShopifyClient(
        allow_network=True,
        shop_domain=shop_domain,
        access_token_secret_id=access_token_secret_id,
    )
    token, reason = client._load_access_token()  # type: ignore[attr-defined]
    if not token:
        return {
            "status": "FAIL",
            "details": f"missing_token ({reason or 'unknown'})",
            "next_action": "Check Shopify token secret + AWS access.",
        }
    url = client._build_url("graphql.json", None)  # type: ignore[attr-defined]
    body = json.dumps({"query": "query { shop { name } }"}).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-shopify-access-token": token,
    }
    try:
        response = client.transport.send(
            ShopifyTransportRequest(
                method="POST",
                url=url,
                headers=headers,
                body=body,
                timeout=client.timeout_seconds,
            )
        )
    except Exception as exc:
        return {
            "status": "FAIL",
            "details": f"request_failed ({exc.__class__.__name__})",
            "next_action": "Verify Shopify connectivity + allow network reads.",
        }
    if response.status_code == 200:
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except Exception:
            payload = None
        if isinstance(payload, dict) and payload.get("errors"):
            return {
                "status": "FAIL",
                "details": "graphql_errors",
                "next_action": "Review Shopify GraphQL permissions + token scopes.",
            }
        return {"status": "PASS", "details": "ok (200)"}
    if response.status_code in {401, 403}:
        return {
            "status": "FAIL",
            "details": f"auth_fail ({response.status_code})",
            "next_action": "Check Shopify token secret; ensure read-only scopes.",
        }
    if response.status_code == 429:
        return {
            "status": "FAIL",
            "details": "rate_limited (429)",
            "next_action": "Retry after cooldown or lower request rate.",
        }
    return {
        "status": "FAIL",
        "details": f"http_error ({response.status_code})",
        "next_action": "Check Shopify API availability + token validity.",
    }


def _check_refresh_lambda_last_success(
    *, env_name: str, window_hours: int = 8
) -> Dict[str, str]:
    if boto3 is None:
        return {
            "status": "WARN",
            "details": "boto3_unavailable",
            "next_action": "Install boto3 or run in CI with AWS creds to verify refresh job.",
        }
    log_group_override = os.environ.get("SHOPIFY_REFRESH_LOG_GROUP")
    lambda_name_override = os.environ.get("SHOPIFY_REFRESH_LAMBDA_NAME")
    canonical_env = _canonical_env(env_name)
    lambda_name = (
        lambda_name_override
        or f"rp-mw-{canonical_env}-shopify-token-refresh"
    )
    log_group = log_group_override or f"/aws/lambda/{lambda_name}"
    client = boto3.client("logs")
    now = datetime.now(timezone.utc)
    try:
        streams = client.describe_log_streams(
            logGroupName=log_group,
            orderBy="LastEventTime",
            descending=True,
            limit=5,
        ).get("logStreams", [])
    except (BotoCoreError, ClientError, Exception) as exc:
        return {
            "status": "FAIL",
            "details": f"log_query_failed ({exc.__class__.__name__})",
            "next_action": "Verify CloudWatch Logs permissions and log group name.",
        }
    latest_ts: Optional[int] = None
    refresh_disabled_ts: Optional[int] = None
    for stream in streams:
        stream_name = stream.get("logStreamName")
        if not stream_name:
            continue
        try:
            response = client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                limit=50,
                startFromHead=False,
            )
        except (BotoCoreError, ClientError, Exception):
            continue
        for event in response.get("events") or []:
            message = event.get("message") or ""
            if "refresh_succeeded" not in message:
                continue
            try:
                payload = json.loads(message)
            except Exception:
                payload = None
            if isinstance(payload, dict):
                ts = event.get("timestamp")
                if payload.get("refresh_succeeded") is True and isinstance(ts, int):
                    latest_ts = ts if latest_ts is None else max(latest_ts, ts)
                if (
                    payload.get("refresh_attempted") is False
                    and payload.get("refresh_error") == "refresh_disabled"
                    and isinstance(ts, int)
                ):
                    refresh_disabled_ts = (
                        ts
                        if refresh_disabled_ts is None
                        else max(refresh_disabled_ts, ts)
                    )
    if latest_ts is None and refresh_disabled_ts is not None:
        last_ts = datetime.fromtimestamp(
            refresh_disabled_ts / 1000, tz=timezone.utc
        )
        age_hours = (now - last_ts).total_seconds() / 3600.0
        return {
            "status": "WARN",
            "details": f"refresh_disabled last_seen_age_hours={age_hours:.2f}",
            "next_action": "Enable SHOPIFY_REFRESH_ENABLED only if rotation is required.",
        }
    if latest_ts is None:
        return {
            "status": "FAIL",
            "details": "no_success_event_found",
            "next_action": "Confirm refresh Lambda is deployed and running.",
        }
    last_ts = datetime.fromtimestamp(latest_ts / 1000, tz=timezone.utc)
    age_hours = (now - last_ts).total_seconds() / 3600.0
    if age_hours > window_hours:
        return {
            "status": "FAIL",
            "details": f"last_success_age_hours={age_hours:.2f}",
            "next_action": "Investigate refresh Lambda failures or scheduling.",
        }
    return {
        "status": "PASS",
        "details": f"last_success_age_hours={age_hours:.2f}",
    }

def _check_richpanel(
    *,
    base_url: Optional[str],
    api_key_secret_id: Optional[str],
) -> Dict[str, str]:
    client = RichpanelClient(
        base_url=base_url,
        api_key_secret_id=api_key_secret_id,
        dry_run=False,
        read_only=True,
    )
    try:
        preflight_path = os.environ.get("RICHPANEL_PREFLIGHT_PATH") or "/v1/users"
        response = client.request("GET", preflight_path, log_body_excerpt=False)
    except (RichpanelRequestError, TransportError, SecretLoadError) as exc:
        return {
            "status": "FAIL",
            "details": f"request_failed ({exc.__class__.__name__})",
            "next_action": "Verify Richpanel API key secret + AWS region/credentials.",
        }
    except Exception as exc:
        return {
            "status": "FAIL",
            "details": f"request_failed ({exc.__class__.__name__})",
            "next_action": "Verify Richpanel API key secret + network egress.",
        }
    if response.dry_run:
        return {
            "status": "FAIL",
            "details": f"dry_run ({response.status_code})",
            "next_action": "Enable Richpanel outbound reads and confirm API key secret.",
        }
    if 200 <= response.status_code < 300:
        return {"status": "PASS", "details": f"ok ({response.status_code})"}
    if response.status_code in {401, 403}:
        return {
            "status": "FAIL",
            "details": f"auth_fail ({response.status_code})",
            "next_action": "Check Richpanel API key secret; rotate if expired.",
        }
    if response.status_code == 429:
        return {
            "status": "FAIL",
            "details": "rate_limited (429)",
            "next_action": "Retry after cooldown or reduce request burst.",
        }
    return {
        "status": "FAIL",
        "details": f"http_error ({response.status_code})",
        "next_action": "Inspect Richpanel API status + verify base URL.",
    }


def _check_shopify(
    *,
    shop_domain: Optional[str],
    access_token_secret_id: Optional[str],
) -> Dict[str, Any]:
    client = ShopifyClient(
        allow_network=True,
        shop_domain=shop_domain,
        access_token_secret_id=access_token_secret_id,
    )
    try:
        response = client.get_shop(safe_mode=False, automation_enabled=True)
    except (ShopifyRequestError, ShopifyTransportError) as exc:
        return {
            "status": "FAIL",
            "details": f"request_failed ({exc.__class__.__name__})",
            "next_action": "Verify Shopify API token secret + network egress.",
        }
    except Exception as exc:
        return {
            "status": "FAIL",
            "details": f"request_failed ({exc.__class__.__name__})",
            "next_action": "Verify Shopify API token secret + network egress.",
        }
    diagnostics = client.token_diagnostics()
    if response.dry_run:
        return {
            "status": "FAIL",
            "details": f"dry_run ({response.reason or 'unknown'})",
            "next_action": "Confirm Shopify token secret + AWS access.",
            "token_diagnostics": diagnostics,
        }
    if 200 <= response.status_code < 300:
        return {
            "status": "PASS",
            "details": f"ok ({response.status_code})",
            "token_diagnostics": diagnostics,
        }
    if response.status_code in {401, 403}:
        return {
            "status": "FAIL",
            "details": f"auth_fail ({response.status_code})",
            "next_action": "Token expired: run refresh job or update secret.",
            "token_diagnostics": diagnostics,
        }
    if response.status_code == 429:
        return {
            "status": "FAIL",
            "details": "rate_limited (429)",
            "next_action": "Retry after cooldown or adjust Shopify rate limits.",
            "token_diagnostics": diagnostics,
        }
    return {
        "status": "FAIL",
        "details": f"http_error ({response.status_code})",
        "next_action": "Check Shopify connectivity + API status.",
        "token_diagnostics": diagnostics,
    }


def _check_refresh_lambda_config() -> Dict[str, str]:
    infra_path = ROOT / "infra" / "cdk" / "lib" / "richpanel-middleware-stack.ts"
    if not infra_path.exists():
        return {
            "status": "SKIP",
            "details": "infra_config_not_found",
            "next_action": "Confirm token refresh Lambda is deployed in IaC.",
        }
    content = infra_path.read_text(encoding="utf-8")
    if "ShopifyTokenRefreshLambda" in content or "shopify-token-refresh" in content:
        return {"status": "PASS", "details": "lambda_config_present"}
    return {
        "status": "WARN",
        "details": "lambda_config_missing",
        "next_action": "Ensure token refresh Lambda is configured for prod.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Order status preflight health check (read-only)."
    )
    parser.add_argument("--env", help="Environment override for secrets paths.")
    parser.add_argument("--out-md", help="Optional markdown output path.")
    parser.add_argument("--shop-domain", help="Shopify shop domain override.")
    parser.add_argument(
        "--shopify-secret-id",
        help="Secret id override for Shopify admin_api_token.",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Secret id override for Richpanel API key.",
    )
    parser.add_argument(
        "--richpanel-base-url", help="Richpanel API base URL override."
    )
    parser.add_argument(
        "--skip-refresh-lambda-check",
        action="store_true",
        help="Skip the optional Shopify token refresh Lambda config check.",
    )
    parser.add_argument(
        "--skip-secrets-check",
        action="store_true",
        help="Skip Secrets Manager existence/decrypt checks.",
    )
    parser.add_argument(
        "--refresh-lambda-window-hours",
        type=int,
        default=8,
        help="Alert window for Shopify refresh Lambda last success.",
    )
    args = parser.parse_args()

    if args.env:
        os.environ["ENVIRONMENT"] = args.env

    checks: List[Dict[str, Any]] = []
    env_name, _ = resolve_env_name()
    checks.append({"name": "required_env", **_check_required_env()})
    if not args.skip_secrets_check:
        checks.append(
            {"name": "required_secrets", **_check_secrets(env_name=env_name)}
        )
    richpanel_result = _check_richpanel(
        base_url=args.richpanel_base_url,
        api_key_secret_id=args.richpanel_secret_id,
    )
    checks.append({"name": "richpanel_api", **richpanel_result})

    shopify_result = _check_shopify(
        shop_domain=args.shop_domain,
        access_token_secret_id=args.shopify_secret_id,
    )
    checks.append({"name": "shopify_token", **shopify_result})
    checks.append(
        {
            "name": "shopify_graphql",
            **_check_shopify_graphql(
                shop_domain=args.shop_domain,
                access_token_secret_id=args.shopify_secret_id,
            ),
        }
    )

    if not args.skip_refresh_lambda_check:
        lambda_result = _check_refresh_lambda_config()
        checks.append({"name": "shopify_token_refresh_lambda", **lambda_result})
        checks.append(
            {
                "name": "shopify_token_refresh_last_success",
                **_check_refresh_lambda_last_success(
                    env_name=env_name,
                    window_hours=args.refresh_lambda_window_hours,
                ),
            }
        )

    overall_status = (
        "PASS"
        if all(entry.get("status") != "FAIL" for entry in checks)
        else "FAIL"
    )
    token_diagnostics = shopify_result.get("token_diagnostics")
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "checks": checks,
        "shopify_token_diagnostics": token_diagnostics,
    }

    print(f"overall_status {overall_status}")
    for entry in checks:
        print(f"{entry.get('name')} {entry.get('status')} {entry.get('details')}")
        if entry.get("next_action"):
            print(f"next_action {entry.get('name')} {entry.get('next_action')}")

    if args.out_md:
        _write_markdown(Path(args.out_md), payload)

    return 0 if overall_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
