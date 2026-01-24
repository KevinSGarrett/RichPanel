# Live Read-Only Shadow Eval Report (B54-C)

## Status
- Run status: completed (workflow_dispatch).
- Target: production (read-only).
- Run ID: `RUN_20260124_0431Z`
- Generated (UTC): 2026-01-24T04:31:28.258422+00:00
- Workflow run: https://github.com/KevinSGarrett/RichPanel/actions/runs/21309232168

## Run parameters
- Sample mode: explicit ticket IDs
- Tickets requested: 6
- Script: `scripts/live_readonly_shadow_eval.py`
- Workflow: `.github/workflows/shadow_live_readonly_eval.yml`
- Inputs: `ticket-ids` (provided out-of-band), `use-aws-secrets=true`, `shop-domain` set

## Sanitized outputs
- JSON report: `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260124_0431Z.json`
- Markdown report: `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260124_0431Z.md`
- HTTP trace: `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_RUN_20260124_0431Z.json`

## Results summary
- Tickets scanned: 6
- Orders matched: 0
- Tracking found: 0
- ETA available: 0
- Errors: 0
- Shopify probe: enabled, `status_code=401`, `ok=false`

## Verification checklist
- `counts.tickets_scanned` equals requested sample size.
- `http_trace_summary.allowed_methods_only` is `true` (GET only; 19 requests).
- `http_trace_summary.services.shopify` equals `1` (probe GET captured).
- No customer identifiers or message bodies appear in artifacts.
