# Live Read-Only Shadow Eval Report (B54-C)

## Status
- Run status: not executed in this workspace (use workflow dispatch).
- Target: production (read-only).

## Planned run parameters
- Sample size: 10
- Script: `scripts/live_readonly_shadow_eval.py`
- Workflow: `.github/workflows/shadow_live_readonly_eval.yml`

## Expected sanitized outputs
- JSON report: `artifacts/readonly_shadow/live_readonly_shadow_eval_report_<RUN_ID>.json`
- Markdown report: `artifacts/readonly_shadow/live_readonly_shadow_eval_report_<RUN_ID>.md`
- HTTP trace: `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_<RUN_ID>.json`

## Verification checklist
- `counts.tickets_scanned` equals requested sample size (or fewer with a warning).
- `http_trace_summary.allowed_methods_only` is `true`.
- No customer identifiers or message bodies appear in artifacts.

## How to run
- Dispatch the workflow with shop domain + sample size; see `REHYDRATION_PACK/RUNS/B54/C/EVIDENCE.md`.
