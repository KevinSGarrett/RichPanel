# Order status preflight health check

- timestamp_utc: 2026-02-02T03:19:18.358828+00:00
- overall_status: FAIL

## Checks
- richpanel_api: PASS — ok (200)
- shopify_token: FAIL — auth_fail (401)
  - next_action: Token expired: run refresh job or update secret.
- shopify_token_refresh_lambda: PASS — lambda_config_present

## Shopify token diagnostics
```
{
  "expired": null,
  "expires_at": null,
  "has_refresh_token": false,
  "raw_format": "json",
  "source_secret_id": "rp-mw/prod/shopify/admin_api_token",
  "status": "loaded",
  "token_type": "offline"
}
```
