# B74/C Run Report — Prod Shadow Canary + Regression Guard

## Scope
- Run a read-only prod shadow canary (200 tickets) with strict throttling.
- Compare key metrics against the B73 baseline.
- Add deterministic regression guard tests + fixtures.
- Update runbook documentation for canary usage.

## Canary Run (read-only)
**Command (PowerShell):**
```
$env:AWS_PROFILE="rp-admin-prod"
$env:AWS_REGION="us-east-2"
$env:AWS_DEFAULT_REGION="us-east-2"
$env:RICHPANEL_ENV="prod"
$env:MW_ENV="prod"
$env:ENVIRONMENT="prod"
$env:RICH_PANEL_ENV="prod"
$env:MW_ALLOW_NETWORK_READS="true"
$env:RICHPANEL_READ_ONLY="true"
$env:RICHPANEL_WRITE_DISABLED="true"
$env:RICHPANEL_OUTBOUND_ENABLED="false"
$env:SHOPIFY_OUTBOUND_ENABLED="true"
$env:SHOPIFY_WRITE_DISABLED="true"
$env:MW_OPENAI_ROUTING_ENABLED="true"
$env:MW_OPENAI_INTENT_ENABLED="true"
$env:MW_OPENAI_SHADOW_ENABLED="true"
$env:OPENAI_ALLOW_NETWORK="true"
$env:RICHPANEL_RATE_LIMIT_RPS="1.0"
python scripts\prod_shadow_order_status_report.py `
  --ticket-refs-path REHYDRATION_PACK\RUNS\B74\C\PROOF\ticket_refs_200.txt `
  --retry-diagnostics --request-trace `
  --batch-size 25 --batch-delay-seconds 1 --throttle-seconds 0 `
  --allow-ticket-fetch-failures --env prod `
  --richpanel-secret-id rp-mw/prod/richpanel/api_key `
  --shopify-secret-id rp-mw/prod/shopify/admin_api_token `
  --shop-domain scentimen-t.myshopify.com `
  --out-json REHYDRATION_PACK\RUNS\B74\C\PROOF\prod_shadow_canary_200.json `
  --out-md REHYDRATION_PACK\RUNS\B74\C\PROOF\prod_shadow_canary_200.md
```

**Artifacts:**
- `REHYDRATION_PACK/RUNS/B74/C/PROOF/prod_shadow_canary_200.json`
- `REHYDRATION_PACK/RUNS/B74/C/PROOF/prod_shadow_canary_200.md`

## Baseline Comparison (B73 → B74)
Baseline report: `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.md`

Key comparisons are embedded in:
- `REHYDRATION_PACK/RUNS/B74/C/PROOF/prod_shadow_canary_200.md` (table + delta + RED status)

## Regression Guard
- Added PII-free fixtures for order-status patterns.
- Added unit tests to lock in order-number extraction + intent classification acceptance.

## Tests
```
python -m pytest backend/tests/test_order_status_regression_guard.py
```

## Docs Update
- Added canary instructions and interpretation guidance to:
  - `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
