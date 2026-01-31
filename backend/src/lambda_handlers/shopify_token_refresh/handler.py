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
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": client.environment,
        "shop_domain": client.shop_domain,
        "refresh_attempted": True,
        "refresh_succeeded": refreshed,
        "token_diagnostics": diagnostics,
        "error": error,
    }

    print(json.dumps(result, sort_keys=True))
    return result
