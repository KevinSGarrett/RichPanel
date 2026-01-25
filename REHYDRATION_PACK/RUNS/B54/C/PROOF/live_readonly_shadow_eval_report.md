# Live Read-Only Shadow Eval Report (B54-C)

## Status
- Run status: completed (workflow dispatch on PR branch).
- Target: production (read-only).
- Run ID: `RUN_20260124_2150Z`
- Generated (UTC): 2026-01-24T21:50:14.607511+00:00
- Workflow run: https://github.com/KevinSGarrett/RichPanel/actions/runs/21322157644
- Artifact: `live-readonly-shadow-eval` (ID 5245610442)

## Run parameters
- Sample mode: explicit ticket IDs (provided out-of-band; not stored)
- Tickets requested: 4
- Script: `scripts/live_readonly_shadow_eval.py`
- Workflow: `.github/workflows/shadow_live_readonly_eval.yml`

## Sanitized outputs (from workflow artifact)
- JSON report: `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260124_2150Z.json`
- Markdown report: `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260124_2150Z.md`
- HTTP trace: `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_RUN_20260124_2150Z.json`

## Results summary
- Tickets scanned: 4
- Order-status candidates: 1
- Orders matched: 1
- Tracking found: 1
- ETA available: 0
- Errors: 0
- Shopify probe: enabled, `status_code=200`, `ok=true`
- Resolution strategy counts (no PII): `richpanel_order_number=2`, `shopify_email_only=1`, `no_match=1`

## Outcome table (PII-safe)
| Ticket slot | Resolution | Confidence | Reason |
| --- | --- | --- | --- |
| 1 | richpanel_order_number | high | shopify_name_match |
| 2 | no_match | low | no_email_available |
| 3 | shopify_email_only | medium | email_only_multiple |
| 4 | richpanel_order_number | high | shopify_name_match |

## Verification checklist
- `counts.tickets_scanned` equals requested sample size.
- `http_trace_summary.allowed_methods_only` is `true` (GET only; 45 requests).
- `http_trace_summary.services.shopify` equals `5` (probe + lookup GETs).
- No customer identifiers, message bodies, or full order numbers appear in artifacts.
