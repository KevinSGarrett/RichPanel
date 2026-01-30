from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from integrations.shopify.client import ShopifyClient  # noqa: E402


def _write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# Shopify health check",
        "",
        f"- timestamp_utc: {payload.get('timestamp_utc')}",
        f"- status_code: {payload.get('status_code')}",
        f"- dry_run: {payload.get('dry_run')}",
        f"- reason: {payload.get('reason')}",
        "",
        "## Token diagnostics",
        "```",
        json.dumps(payload.get("token_diagnostics"), indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Shopify health check.")
    parser.add_argument("--shop-domain", help="Shopify shop domain override.")
    parser.add_argument(
        "--shopify-secret-id",
        help="Secret id override for Shopify admin_api_token.",
    )
    parser.add_argument(
        "--out-md",
        help="Optional markdown output path for proof artifacts.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh the access token before the health check.",
    )
    args = parser.parse_args()

    client = ShopifyClient(
        allow_network=True,
        shop_domain=args.shop_domain,
        access_token_secret_id=args.shopify_secret_id,
    )

    if args.refresh:
        refreshed = client.refresh_access_token()
        if not refreshed:
            print("refresh_failed")

    response = client.get_shop(safe_mode=False, automation_enabled=True)
    diagnostics = client.token_diagnostics()

    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status_code": response.status_code,
        "dry_run": response.dry_run,
        "reason": response.reason,
        "token_diagnostics": diagnostics,
    }

    if args.out_md:
        _write_markdown(Path(args.out_md), result)

    if response.dry_run:
        print("dry_run", response.reason or "unknown")
        return 2
    if 200 <= response.status_code < 300:
        print("ok", response.status_code)
        return 0
    print("failed", response.status_code)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
