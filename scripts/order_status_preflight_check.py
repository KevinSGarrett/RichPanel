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

from integrations.shopify.client import (  # noqa: E402
    ShopifyClient,
    ShopifyRequestError,
    TransportError as ShopifyTransportError,
)
from richpanel_middleware.integrations.richpanel.client import (  # noqa: E402
    RichpanelClient,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)


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
        response = client.request("GET", "/v1/users", log_body_excerpt=False)
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
    args = parser.parse_args()

    if args.env:
        os.environ["ENVIRONMENT"] = args.env

    checks: List[Dict[str, Any]] = []
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

    if not args.skip_refresh_lambda_check:
        lambda_result = _check_refresh_lambda_config()
        checks.append({"name": "shopify_token_refresh_lambda", **lambda_result})

    overall_status = (
        "PASS"
        if all(entry.get("status") == "PASS" for entry in checks)
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
