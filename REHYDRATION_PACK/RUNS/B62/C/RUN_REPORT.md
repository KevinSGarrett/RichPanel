# Run Report — B62/C

## Metadata
- Date (UTC): 2026-01-28
- Run ID: `RUN_20260128_1811Z`
- Environment: `prod` (read-only)
- Status: `WARN` (schema drift alert; gate blocked)
- Workspace: `C:\RichPanel_GIT`

## Objective
Move live read-only shadow validation into a repeatable report + CI gate with read-only guarantees.

## Summary
- ticket_count: 17; match_success_rate: 100.0%
- tracking_or_eta_available_rate: 100.0%; would_reply_send: false
- match_methods: order_number=11, name_email=3, email_only=3
- match_failure_buckets: all zero
- run_warnings: none
- shopify_probe.status_code: 200
- http_trace_summary.allowed_methods_only: true; drift_watch.has_alerts: true

## Artifacts
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.md`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_http_trace.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/generate_sample_report.py`

## Notes
- Run executed via `Shadow Live Read-Only Eval` workflow (run `21450058346`).
- `RICHPANEL_OUTBOUND_ENABLED=false` enforced in workflow and script.
