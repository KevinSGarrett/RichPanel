# B59/C Changes

## Ops / Secrets
- Updated AWS Secrets Manager `rp-mw/prod/shopify/admin_api_token` from placeholder to an active
  Shopify Admin API token (aligned with the single-store setup).

## Validation
- Re-ran `scripts/live_readonly_shadow_eval.py` in prod read-only mode with explicit ticket IDs
  and Shopify probe enabled (run id `RUN_20260126_2030Z`).

## Docs
- Updated `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md` with secret paths, token
  validation steps, and common 401/403 failure modes.
