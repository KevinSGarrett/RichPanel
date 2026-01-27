# Run Report - B60/C

## Metadata
- Date (UTC): 2026-01-27
- Run ID: `RUN_20260127_0338Z`
- Branch: `b60/live-readonly-shadow-metrics`
- Workspace: `C:\RichPanel_GIT`
- Environment: `prod` (read-only)
- Shop domain: `scentimen-t.myshopify.com`
- Tickets evaluated: 0 (ticket listing endpoints returned 403; run continued with allow-empty-sample)

## Objective
Add daily PII-safe metrics, schema drift detection, scheduled CI runs, and summary artifacts for
the live read-only shadow workflow.

## Summary
- Added a PII-safe `summary.json` with match rate, channel counts, timing, and failure rollups.
- Added schema fingerprinting and drift warnings in the eval report.
- Scheduled the workflow daily and ensured summary artifacts are uploaded.
- CI workflow_dispatch run succeeded and uploaded artifacts.

## Artifacts
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_report_RUN_20260127_0338Z.json`
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_summary_RUN_20260127_0338Z.json`
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_http_trace_RUN_20260127_0338Z.json`
- `REHYDRATION_PACK/RUNS/B60/C/PROOF/live_readonly_shadow_eval_report_RUN_20260127_0338Z.md`

## Notes
- Ticket listing endpoints returned 403; the run completed with empty sample and `run_warnings`
  set to `ticket_listing_403`.
- All artifacts are PII-safe (fingerprints only).
