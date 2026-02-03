from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from integrations.shopify.client import ShopifyClient  # noqa: E402


def _safe_token_format(raw_format: Optional[str]) -> str:
    if not raw_format:
        return "unknown"
    if raw_format.lower() == "json":
        return "json"
    return "raw"


def _load_client_credentials(client: ShopifyClient) -> Tuple[bool, bool]:
    try:
        client_id, client_secret = client._load_client_credentials()  # type: ignore[attr-defined]
    except Exception:
        return False, False
    return bool(client_id), bool(client_secret)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Shopify health check.")
    parser.add_argument(
        "--env",
        help="Environment name override (sets ENVIRONMENT for Secrets Manager paths).",
    )
    parser.add_argument("--shop-domain", help="Shopify shop domain override.")
    parser.add_argument(
        "--shopify-secret-id",
        help="Secret id override for Shopify admin_api_token.",
    )
    parser.add_argument(
        "--out-json",
        help="Optional JSON output path for proof artifacts.",
    )
    parser.add_argument(
        "--aws-region",
        help="AWS region override for Secrets Manager calls (ex: us-east-2).",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Attempt to refresh the access token before the health check.",
    )
    parser.add_argument(
        "--refresh-dry-run",
        action="store_true",
        help="Record a refresh attempt without calling Shopify (no secret write).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Emit diagnostic details to stdout.",
    )
    args = parser.parse_args()

    if args.env:
        os.environ["ENVIRONMENT"] = args.env
    if args.aws_region:
        os.environ["AWS_REGION"] = args.aws_region
        os.environ["AWS_DEFAULT_REGION"] = args.aws_region
    if not os.environ.get("AWS_REGION") and not os.environ.get("AWS_DEFAULT_REGION"):
        os.environ["AWS_REGION"] = "us-east-2"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-2"

    client = ShopifyClient(
        allow_network=True,
        shop_domain=args.shop_domain,
        access_token_secret_id=args.shopify_secret_id,
    )

    if args.verbose:
        print("env", client.environment)
        print("shop_domain", client.shop_domain)
        print("secret_ids", ",".join(client._secret_id_candidates))

    refresh_attempted = False
    refresh_succeeded: Optional[bool] = None
    refresh_dry_run = False

    if args.refresh_dry_run:
        refresh_attempted = True
        refresh_dry_run = True
    elif args.refresh:
        refresh_attempted = True
        refresh_succeeded = client.refresh_access_token()

    error: Optional[str] = None
    health_payload: Dict[str, Any] = {}
    try:
        response = client.get_shop(safe_mode=False, automation_enabled=True)
        health_payload = {
            "status_code": response.status_code,
            "dry_run": response.dry_run,
            "reason": response.reason,
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        error = str(exc)
        health_payload = {"error": str(exc)}

    token_diagnostics = client.token_diagnostics()
    has_client_id, has_client_secret = _load_client_credentials(client)
    can_refresh = bool(has_client_id and has_client_secret)
    refresh_mode = "client_credentials"
    if token_diagnostics.get("has_refresh_token"):
        refresh_mode = "refresh_token"

    token_format = _safe_token_format(token_diagnostics.get("raw_format"))
    status = "FAIL"
    if health_payload.get("dry_run"):
        status = "DRY_RUN"
    elif isinstance(health_payload.get("status_code"), int) and 200 <= int(
        health_payload["status_code"]
    ) < 300:
        status = "PASS"

    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": client.environment,
        "shop_domain": client.shop_domain,
        "status": status,
        "health_check": health_payload,
        "token_format": token_format,
        "token_type": token_diagnostics.get("token_type"),
        "expires_at": token_diagnostics.get("expires_at"),
        "expired": token_diagnostics.get("expired"),
        "can_refresh": can_refresh,
        "refresh_mode": refresh_mode,
        "refresh_attempted": refresh_attempted,
        "refresh_succeeded": refresh_succeeded,
        "refresh_dry_run": refresh_dry_run,
        "refresh_error": client.refresh_error(),
        "token_diagnostics": token_diagnostics,
        "secret_id_candidates": list(client._secret_id_candidates),
        "error": error,
    }

    if args.out_json:
        _write_json(Path(args.out_json), result)

    print(json.dumps(result, indent=2, sort_keys=True))

    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
