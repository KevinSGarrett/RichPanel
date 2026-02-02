# Order status preflight health check

- timestamp_utc: 2026-02-02T10:51:36.410801+00:00
- overall_status: PASS

## Checks
- richpanel_api: PASS — ok (200)
- shopify_token: PASS — ok (200)
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
