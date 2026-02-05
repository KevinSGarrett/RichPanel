# Shopify Token Runbook

## Scope
- Read-only Shopify access only (no order writes; no sandbox).
- Covers DEV and PROD secrets and refresh behavior for the Shopify client.

## Where the Shopify secret lives
- **DEV account**: `151124909266` (region: `us-east-2`)
  - Secret: `rp-mw/dev/shopify/admin_api_token`
- **PROD account**: `878145708918` (region: `us-east-2`)
  - Secret: `rp-mw/prod/shopify/admin_api_token`

Related secrets (only needed for OAuth refresh):
- `rp-mw/<env>/shopify/client_id`
- `rp-mw/<env>/shopify/client_secret`
- `rp-mw/<env>/shopify/refresh_token` (legacy; refresh only uses bundle refresh token)

## Supported token formats
### Admin API token (no refresh)
- Secret value is a **plain string**: `shpat_...`
- Refresh is **skipped** and the health check runs only.

### OAuth token bundle (auto-refresh)
- Secret value is **JSON** with a refresh token:
```
{
  "access_token": "shpua_...",
  "refresh_token": "shpua_...",
  "expires_at": 1710000000
}
```
- Refresh runs only when the **bundle contains a non-empty refresh_token**.

## Health check + refresh behavior
- Lambda: `shopify-token-refresh` runs on a schedule (every 4 hours).
- Health check always runs (read-only).
- Refresh is **skipped** for admin tokens and logs `refresh skipped (admin token)`.
- Refresh updates the same `admin_api_token` secret when the bundle is OAuth.

## Fast diagnostics
Run a read-only check and capture AWS account + token format:
```
python scripts/shopify_health_check.py --diagnose --env dev
```

Recommended preflight for AWS account + secrets:
```
python scripts/secrets_preflight.py --env dev --expect-account-id 151124909266
```

## Handling 401 / 403
- **401 Unauthorized**
  - Token is invalid/expired or the wrong account/secret was used.
  - Confirm the secret exists in the correct AWS account and region.
  - For OAuth bundles, ensure `refresh_token` is present in the JSON.
- **403 Forbidden**
  - Token lacks required scopes.
  - Re-issue the token with correct Shopify app scopes (read-only).

## Notes
- Secrets are **account-specific** and not shared across DEV/PROD.
- Never paste tokens into PROD or commit tokens to the repo.
