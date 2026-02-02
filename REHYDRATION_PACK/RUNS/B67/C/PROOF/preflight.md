# Order status preflight health check

- timestamp_utc: 2026-02-02T15:22:59.786249+00:00
- overall_status: PASS

## Checks
- required_env: PASS — env=prod source=RICHPANEL_ENV
- required_secrets: PASS — checked=5
- richpanel_api: PASS — ok (200)
- shopify_token: PASS — ok (200)
- shopify_graphql: PASS — ok (200)
- shopify_token_refresh_lambda: PASS — lambda_config_present
- shopify_token_refresh_last_success: PASS — last_success_age_hours=0.07

## Shopify token diagnostics
```
{
  "expired": false,
  "expires_at": 1770131928.959342,
  "has_refresh_token": false,
  "raw_format": "json",
  "source_secret_id": "rp-mw/prod/shopify/admin_api_token",
  "status": "loaded",
  "token_type": "offline"
}
```
