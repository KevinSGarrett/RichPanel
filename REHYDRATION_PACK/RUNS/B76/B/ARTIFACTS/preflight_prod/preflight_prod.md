# Order status preflight health check

- timestamp_utc: 2026-02-10T17:05:35.879935+00:00
- overall_status: FAIL
- bot_agent_id_secret_present: False
- bot_agent_id_secret_checked: True

## Checks
- required_env: FAIL — missing=MW_ALLOW_NETWORK_READS,RICHPANEL_OUTBOUND_ENABLED,RICHPANEL_READ_ONLY,RICHPANEL_WRITE_DISABLED,SHOPIFY_OUTBOUND_ENABLED,SHOPIFY_SHOP_DOMAIN,SHOPIFY_WRITE_DISABLED
  - next_action: Set required env vars and safety flags for read-only preflight.
- required_secrets: PASS — checked=5
- bot_agent_id_secret: FAIL — missing_or_unreadable (ResourceNotFoundException)
  - next_action: Create bot agent in Richpanel and store id into Secrets Manager at rp-mw/prod/richpanel/bot_agent_id.
- richpanel_api: PASS — ok (200)
- shopify_token: PASS — ok (200)
- shopify_graphql: PASS — ok (200)
- shopify_token_refresh_lambda: PASS — lambda_config_present
- shopify_token_refresh_last_success: FAIL — log_query_failed (ResourceNotFoundException)
  - next_action: Verify CloudWatch Logs permissions and log group name.

## Shopify token diagnostics
```
{
  "expired": null,
  "expires_at": null,
  "has_refresh_token": false,
  "raw_format": "json",
  "refresh_token_source": null,
  "source_secret_id": "rp-mw/prod/shopify/admin_api_token",
  "status": "loaded",
  "token_type": "offline"
}
```
