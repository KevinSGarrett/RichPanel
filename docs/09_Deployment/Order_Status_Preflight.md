# Order Status Preflight (Prod)

## Purpose

Run a **read-only** preflight before enabling Order Status outbound in production. The script validates:

- Required env vars and safety flags
- Secrets Manager entries exist and decrypt
- Richpanel GET connectivity
- Shopify REST + GraphQL read checks
- Shopify token refresh Lambda recent success

---

## Prereqs

- AWS credentials with:
  - `secretsmanager:GetSecretValue`
  - `logs:FilterLogEvents`
- Environment is set to prod (`ENVIRONMENT=prod` or `RICHPANEL_ENV=prod`)
- PII-safe execution (do not paste outputs containing PII)

---

## Required env flags (safe read-only)

```powershell
$env:ENVIRONMENT = "prod"
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_READ_ONLY = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "false"
$env:SHOPIFY_OUTBOUND_ENABLED = "true"
$env:SHOPIFY_WRITE_DISABLED = "true"
$env:SHOPIFY_SHOP_DOMAIN = "<shop>.myshopify.com"
```

Optional overrides:

- `RICHPANEL_API_KEY_SECRET_ID`
- `SHOPIFY_ACCESS_TOKEN_SECRET_ID`
- `SHOPIFY_REFRESH_LAMBDA_NAME` or `SHOPIFY_REFRESH_LOG_GROUP`

---

## Command

```powershell
python scripts/preflight_order_status_prod.py `
  --env prod `
  --out-md artifacts/preflight/order_status_preflight.md
```

**Expected:** `overall_status PASS`

If **FAIL**, follow the `next_action` guidance printed for each check.

---

## Output

- Console output:
  - `overall_status PASS|FAIL`
  - per-check status + details
- Optional markdown proof:
  - `artifacts/preflight/order_status_preflight.md`

---

## Common failures

- `required_env FAIL`: missing safety flags or shop domain.
- `required_secrets FAIL`: missing or undecryptable secret ids.
- `shopify_graphql FAIL`: token scope issue or rate limit.
- `shopify_token_refresh_last_success FAIL`: refresh job not running in last 8h.

---

## Optional skips (diagnostic only)

Use these only for **debug** (not for prod sign-off):

- `--skip-secrets-check`
- `--skip-refresh-lambda-check`
