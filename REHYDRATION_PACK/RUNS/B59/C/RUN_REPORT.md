# Run Report - B59/C

## Metadata
- Date (UTC): 2026-01-26
- Run ID: `RUN_20260126_2030Z`
- Branch: `b59/prod-shopify-token-shadow-rerun`
- Workspace: `C:\RichPanel_GIT`
- Environment: `prod` (read-only)
- Shop domain: `scentimen-t.myshopify.com`
- Tickets evaluated: 17 (explicit IDs; ticket listing endpoints returned 403)

## Objective
Fix the prod Shopify token and rerun the live read-only shadow validation using prod
Richpanel + prod Shopify credentials (no writes).

## Summary
- Prod Shopify secret `rp-mw/prod/shopify/admin_api_token` was a placeholder; updated to the active Shopify token.
- Live read-only shadow eval completed with write blocks enabled; Shopify probe returned 200.
- 17 tickets scanned; 17 matched (0 unmatched); tracking found in 11; ETA available in 17.
- HTTP trace shows GET-only for Richpanel/Shopify/ShipStation and AWS POSTs limited to SecretsManager GetSecretValue.

## Artifacts
- `REHYDRATION_PACK/RUNS/B59/C/REPORT/shadow_readonly_report.md`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_2030Z.json`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_2030Z.md`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_RUN_20260126_2030Z.json`

## Notes
- Richpanel conversation endpoints returned 403 for several tickets; ticket reads still succeeded.
- Ticket identifiers are hashed in artifacts; no PII stored.
- Decision (B59/C): prod Shopify secret is aligned to the dev token (single-store setup).
