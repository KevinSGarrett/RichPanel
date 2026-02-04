from __future__ import annotations

import json
from datetime import datetime, timezone

from integrations.shopify.client import ShopifyClient


def lambda_handler(event, context):
    client = ShopifyClient(allow_network=True)
    refreshed = False
    error = None
    try:
        refreshed = client.refresh_access_token()
    except Exception as exc:  # pragma: no cover - defensive logging
        error = str(exc)

    diagnostics = client.token_diagnostics()
    health = None
    try:
        response = client.get_shop(safe_mode=False, automation_enabled=True)
        health = {
            "status_code": response.status_code,
            "dry_run": response.dry_run,
            "reason": response.reason,
            "url": response.url,
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        health = {"error": str(exc)}
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": client.environment,
        "shop_domain": client.shop_domain,
        "refresh_attempted": True,
        "refresh_succeeded": refreshed,
        "refresh_error": client.refresh_error(),
        "token_diagnostics": diagnostics,
        "health_check": health,
        "error": error,
    }

    print(json.dumps(result, sort_keys=True))
    return result
