# Order status preflight health check

- timestamp_utc: 2026-02-10T18:33:43.372018+00:00
- overall_status: FAIL
- bot_agent_id_secret_present: True
- bot_agent_id_secret_checked: True

## Checks
- required_env: FAIL — missing=MW_ALLOW_NETWORK_READS,RICHPANEL_OUTBOUND_ENABLED,RICHPANEL_READ_ONLY,RICHPANEL_WRITE_DISABLED,SHOPIFY_OUTBOUND_ENABLED,SHOPIFY_SHOP_DOMAIN,SHOPIFY_WRITE_DISABLED
  - next_action: Set required env vars and safety flags for read-only preflight.
- required_secrets: PASS — checked=5
- bot_agent_id_secret: PASS — present (rp-mw/prod/richpanel/bot_agent_id)
- richpanel_api: PASS — ok (200)
- shopify_token: PASS — ok (200)
- shopify_graphql: PASS — ok (200)
- shopify_token_refresh_lambda: PASS — lambda_config_present
- shopify_token_refresh_last_success: PASS — last_success_age_hours=1.87

## Shopify token diagnostics
```
{
  "expired": false,
  "expires_at": 1770828079.2729716,
  "has_refresh_token": false,
  "raw_format": "json",
  "refresh_token_source": null,
  "source_secret_id": "rp-mw/prod/shopify/admin_api_token",
  "status": "loaded",
  "token_type": "offline"
}
```
