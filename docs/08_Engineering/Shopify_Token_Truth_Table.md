# Shopify Token Truth Table

## Purpose
Define which Shopify tokens we use in DEV/STAGING/PROD, how they expire, where they live, and how to validate them quickly.

## Token types and behavior
Shopify tokens fall into two supported types:

- **Offline Admin API token (`shpat_...`)**
  - Long-lived (no planned expiry).
  - Can still be **revoked/rotated** unexpectedly (app uninstall, manual rotation).
  - Stored as a **plain string** in Secrets Manager.
- **OAuth access token bundle (`shpua_...`)**
  - **Expires** on a schedule (expected).
  - Stored as **JSON** with `access_token`, `refresh_token`, and optional `expires_at`.
  - Can still be **revoked/rotated** unexpectedly (app uninstall, secret overwrite).

## Token truth table (DEV / STAGING / PROD)
| Environment | Expected token type | Expected expiry | Unexpected failure modes | AWS Secrets Manager (source of truth) | GitHub Actions secrets |
|---|---|---|---|---|---|
| DEV | Offline Admin API token (default) | No planned expiry | Revoked, rotated, or overwritten | `rp-mw/dev/shopify/admin_api_token` | Optional: `DEV_SHOPIFY_SHOP_DOMAIN` for shop domain |
| STAGING | Offline Admin API token (default) | No planned expiry | Revoked, rotated, or overwritten | `rp-mw/staging/shopify/admin_api_token` | Optional: `STAGING_SHOPIFY_SHOP_DOMAIN` for shop domain |
| PROD | Offline Admin API token (default) | No planned expiry | Revoked, rotated, or overwritten | `rp-mw/prod/shopify/admin_api_token` | `PROD_SHOPIFY_SHOP_DOMAIN` for shop domain |

Notes:
- OAuth bundles are permitted **only** when refresh is explicitly enabled and the JSON bundle contains a valid `refresh_token`.
- Legacy fallback secret (not preferred): `rp-mw/<env>/shopify/access_token`.

## How to determine token type (quick)
1) **Check the secret format** in AWS Secrets Manager:
   - Plain string starting with `shpat_` → offline Admin API token.
   - JSON with `access_token` and `refresh_token` → OAuth bundle.
2) **Use the diagnostic health check**:
```
python scripts/shopify_health_check.py --diagnose --env <dev|staging|prod> --shop-domain <shop>.myshopify.com
```
This reports `token_type`, `token_format`, and refresh capability without exposing the token.

## Quick validation (prove auth works)
Use the lightweight env-token health check:
```
SHOPIFY_ACCESS_TOKEN=<token> SHOPIFY_SHOP_DOMAIN=<shop>.myshopify.com \
python scripts/shopify_token_healthcheck.py
```

Or with curl:
```
curl -sS -o /dev/null -w "%{http_code}\n" \
  -H "X-Shopify-Access-Token: <token>" \
  "https://<shop>.myshopify.com/admin/api/2024-01/shop.json"
```

Expected result:
- `200` means token is valid for read-only access.

## What to do on failure
### 401 Unauthorized
- Token is invalid/expired or the wrong secret/account was used.
- Confirm AWS account + region and the secret id in Secrets Manager.
- If OAuth bundle: ensure `refresh_token` is present and refresh is enabled.
- If Admin token: re-issue a new Admin API token and update the secret.

### 403 Forbidden
- Token lacks required scopes.
- Re-issue token with correct Shopify app scopes (read-only).

### 429 Too Many Requests
- Rate limit hit; retry after cooldown.
- For CI guardrails, treat as a hard fail to avoid masking auth problems.

### Network / request errors
- Verify `SHOPIFY_SHOP_DOMAIN` is correct and reachable.
- Verify CI runners have outbound access to Shopify.

## Operational workflow (do not re-add secrets blindly)
1) **Run health checks first** (fast fail):
   - `python scripts/shopify_token_healthcheck.py`
   - `python scripts/shopify_health_check.py --diagnose --env <env> --shop-domain <shop>.myshopify.com`
2) **Confirm token type + source**:
   - Inspect the Secrets Manager secret format (`shpat_...` vs JSON bundle).
3) **Only rotate when needed**:
   - If Admin token is revoked, issue a new Admin API token and update the secret.
   - If OAuth token expired, ensure `refresh_token` is present and refresh is enabled.
4) **Re-run health checks** to confirm status is `PASS` / `OK`.
5) **Record proof** in `REHYDRATION_PACK/RUNS/<run>/PROOF/`.
