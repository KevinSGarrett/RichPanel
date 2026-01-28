# Run Report — B62/C

## Metadata
- Date (UTC): 2026-01-28
- Run ID: `RUN_20260128_1637Z`
- Environment: `prod` (read-only)
- Status: `WARN` (ticket_fetch_failed + drift alerts; gate blocked)
- Workspace: `C:\RichPanel_GIT`

## Objective
Move live read-only shadow validation into a repeatable report + CI gate with read-only guarantees.

## Summary
- ticket_count: 17; match_success_rate: 0.0%
- tracking_or_eta_available_rate: 0.0%; would_reply_send: false
- match_failure_buckets: no_order_candidates=6, no_order_number=3, other_failure=8
- top_failure_reasons: no_order_candidates=9, ticket_fetch_failed=8
- run_warnings: ticket_fetch_failed
- shopify_probe.status_code: 401
- http_trace_summary.allowed_methods_only: true; drift_watch.has_alerts: true

## Artifacts
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.md`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_http_trace.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/generate_sample_report.py`

## Notes
- Run executed via `Shadow Live Read-Only Eval` workflow (run `21446879808`).
- `RICHPANEL_OUTBOUND_ENABLED=false` enforced in workflow and script.
