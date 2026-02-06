# Order status preflight health check

- timestamp_utc: 2026-02-06T03:30:55.350029+00:00
- overall_status: PASS
- bot_agent_id_secret_present: True

## Checks
- required_env: PASS — env=dev source=ENVIRONMENT
- required_secrets: PASS — checked=5
- bot_agent_id_secret: PASS — present (rp-mw/dev/richpanel/bot_agent_id)
- richpanel_api: PASS — ok (200)
- shopify_token: PASS — ok (200)
- shopify_graphql: PASS — ok (200)
- shopify_token_refresh_lambda: PASS — lambda_config_present
- shopify_token_refresh_last_success: WARN — log_query_failed (ResourceNotFoundException)
  - next_action: Verify CloudWatch Logs permissions and log group name.

## Shopify token diagnostics
```
{
  "expired": null,
  "expires_at": null,
  "has_refresh_token": false,
  "raw_format": "plain",
  "refresh_token_source": null,
  "source_secret_id": "rp-mw/dev/shopify/admin_api_token",
  "status": "loaded",
  "token_type": "offline"
}
```
