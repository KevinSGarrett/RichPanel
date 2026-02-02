# Order status preflight health check

- timestamp_utc: 2026-02-02T01:44:49.975377+00:00
- overall_status: FAIL

## Checks
- richpanel_api: FAIL — request_failed (SecretLoadError)
  - next_action: Verify Richpanel API key secret + AWS region/credentials.
- shopify_token: FAIL — dry_run (secret_lookup_failed)
  - next_action: Confirm Shopify token secret + AWS access.
- shopify_token_refresh_lambda: PASS — lambda_config_present

## Shopify token diagnostics
```
{
  "status": "unknown"
}
```
