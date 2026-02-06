# ISSUE-003 — Shopify Token Expiry + Refresh

Last updated: 2026-02-05  
Status: Active

## Problem
Shopify token failures are causing Order Status lookups to fail. Confusion persists about whether the token expires and whether refresh is supported.

## Evidence (B72)
Proof artifacts:
- `REHYDRATION_PACK/RUNS/B72/B/PROOF/secrets_preflight_dev.json`
- `REHYDRATION_PACK/RUNS/B72/B/PROOF/secrets_preflight_prod.json`
- `REHYDRATION_PACK/RUNS/B72/B/PROOF/shopify_health_dev.json`
- `REHYDRATION_PACK/RUNS/B72/B/PROOF/shopify_health_prod.json`
- `REHYDRATION_PACK/RUNS/B72/B/PROOF/shopify_health_summary.md`

Key findings:
- **DEV**: secrets preflight failed with `ForbiddenException: No access` (cannot read `rp-mw/dev/shopify/admin_api_token`), so token diagnostics are unavailable and the health check dry-ran (`secret_lookup_failed`).
- **PROD**: token diagnostics show `token_type=offline` and `token_format=json`, but the health check failed with `401 Invalid access token`. There is **no refresh token** (`has_refresh_token=false`), so the token cannot be refreshed automatically.

## Reality Check — Token Types
- **Offline tokens** (`shpat_`) do **not** expire by design.
- **Online tokens** (`shpua_`) **expire** and require a refresh token.
- Refresh is only possible when the admin token is stored as JSON with a `refresh_token`, and when `SHOPIFY_REFRESH_ENABLED=true` plus client id/secret are available.

## Automated Monitoring (Current Direction)
- A scheduled GitHub Action runs every 6 hours for **dev + prod**.
- It reads the Admin API token from Secrets Manager and runs a read-only shop health check.
- If refresh is possible, it will refresh and update Secrets Manager; otherwise it fails loudly to trigger a manual rotation.

## Required Human Actions When Refresh Is Impossible
1. Generate a new read-only Admin API token in Shopify.
2. Update `rp-mw/<env>/shopify/admin_api_token` in AWS Secrets Manager.
3. Re-run `scripts/shopify_health_check.py` to verify `status=PASS`.

## Open Items
- Restore DEV AWS access for profile `rp-admin-dev` (GetRoleCredentials is forbidden).
- Rotate the PROD Admin API token (current token rejected with 401).
