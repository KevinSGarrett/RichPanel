# B69 — Agent B Run Report

Date: 2026-02-04

## Summary
- Confirmed the live-store token is an offline Admin API token (`shpat_`) and does not inherently expire.
- Identified the scheduled refresh flow as the instability source when it overwrites the stable token with a rotating/invalid token.
- Implemented a refresh-token-only rotation path, improved health check status reporting, and shifted prod workflows to AWS Secrets Manager via OIDC.

## Root Cause (evidence-based)
- The token in use is an offline Admin API token (`shpat_`), which does not inherently expire.
- The scheduled refresh path overwrote the stable token in `rp-mw/<env>/shopify/admin_api_token` with a rotating/invalid token.
- When that refreshed token is invalid, Shopify returns `401` from the `shop.json` endpoint.
- Evidence:
  - `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_prod.json` → `token_type=offline`, `status_code=200`
  - `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_invalid.json` → `status_code=401`, error payload captured

## Work Completed
- Shopify refresh now **skips** when no refresh token is present (stable admin token remains untouched).
- Health check returns actionable statuses (`PASS`, `FAIL_INVALID_TOKEN`, `FAIL_FORBIDDEN`, `FAIL_RATE_LIMIT`) plus `--json` mode.
- Added logs for invalid/forbidden responses and refresh success/skip.
- Updated prod workflows to fetch Shopify tokens from AWS Secrets Manager using OIDC by default.
- Updated secrets docs to reflect refresh-token requirement and CI token sourcing strategy.

## Tests Run
- `python -m pytest scripts/test_shopify_health_check.py`
- `python -m pytest scripts/test_shopify_client.py -k "refresh_access_token_returns_false_without_refresh_token or refresh_access_token_client_credentials or refresh_error_includes_error_code"`

## Limitations / Notes
- The invalid-token check uses a deliberately invalid override to capture the real 401 payload (read-only endpoint).
