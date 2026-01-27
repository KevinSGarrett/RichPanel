# Run Report - B60/C

## Metadata
- Date (UTC): 2026-01-27
- Run ID: `RUN_20260127_0434Z`
- Branch: `main`
- Workspace: `C:\RichPanel_GIT`
- Environment: `prod` (read-only)
- Shop domain: `scentimen-t.myshopify.com`
- Tickets evaluated: 17 (explicit IDs via `PROD_RICHPANEL_TICKET_IDS`)

## Objective
Add daily PII-safe metrics, schema drift detection, scheduled CI runs, and summary artifacts for
the live read-only shadow workflow.

## Summary
- Added a PII-safe `summary.json` with match rate, channel counts, timing, and failure rollups.
- Added schema fingerprinting and drift warnings in the eval report.
- Scheduled the workflow daily and ensured summary artifacts are uploaded.
- CI workflow_dispatch run succeeded and uploaded artifacts; drift warning flagged (>20% new ticket schemas).

## Artifacts
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_report_RUN_20260127_0434Z.json`
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_summary_RUN_20260127_0434Z.json`
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_http_trace_RUN_20260127_0434Z.json`
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_report_RUN_20260127_0434Z.md`

## Notes
- Ticket IDs sourced from `PROD_RICHPANEL_TICKET_IDS` to bypass list endpoint 403s.
- `schema_drift.warning=true` due to >20% new ticket schema fingerprints.
- All artifacts are PII-safe (fingerprints only).
