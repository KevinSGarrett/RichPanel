# Run Report — B62/C

## Metadata
- Date (UTC): 2026-01-28
- Run ID (source): `RUN_20260126_0319Z`
- Environment: `prod` (read-only)
- Status: `MANUAL` (sample output derived from prior run; new prod run required)
- Workspace: `C:\RichPanel_GIT`

## Objective
Move live read-only shadow validation into a repeatable report + CI gate with read-only guarantees.

## Summary
- ticket_count: 17; match_success_rate: 94.12%
- tracking_or_eta_available_rate: 94.12%; would_reply_send: false
- match_failure_buckets: unknown=1
- http_trace_summary.allowed_methods_only: true; drift_watch.has_alerts: false

## Artifacts
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.md`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_http_trace.json`
- `REHYDRATION_PACK/RUNS/B62/C/PROOF/generate_sample_report.py`

## Notes
- Sample report generated from `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_0319Z.json`.
- `RICHPANEL_OUTBOUND_ENABLED=false` is now required by `scripts/live_readonly_shadow_eval.py`.
