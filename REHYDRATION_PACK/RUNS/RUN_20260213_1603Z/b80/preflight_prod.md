# Order status preflight health check

- timestamp_utc: 2026-02-13T16:40:16.129578+00:00
- overall_status: PASS
- bot_agent_id_secret_present: True
- bot_agent_id_secret_checked: True

## Checks
- required_env: PASS — env=prod source=ENVIRONMENT
- required_secrets: PASS — checked=5
- bot_agent_id_secret: PASS — present (rp-mw/prod/richpanel/bot_agent_id)
- richpanel_api: PASS — ok (200)
- shopify_token: PASS — ok (200)
- shopify_graphql: PASS — ok (200)

## Shopify token diagnostics
```
{
  "expired": false,
  "expires_at": 1771086387.8318517,
  "has_refresh_token": false,
  "raw_format": "json",
  "refresh_token_source": null,
  "source_secret_id": "rp-mw/prod/shopify/admin_api_token",
  "status": "loaded",
  "token_type": "offline"
}
```
