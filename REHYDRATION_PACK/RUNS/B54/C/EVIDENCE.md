# B54 C Evidence

## Workflow (recommended)
- Workflow: `.github/workflows/shadow_live_readonly_eval.yml`
- Dispatch example:
```
gh workflow run shadow_live_readonly_eval.yml \
  -f sample-size=10 \
  -f shop-domain=<your-shop.myshopify.com>
```
- Optional: provide comma-separated ticket IDs via `-f ticket-ids="<id1>,<id2>"`

## Expected artifacts (from workflow run)
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_<RUN_ID>.json`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_<RUN_ID>.md`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_<RUN_ID>.json`

## Validation checks (PII-safe)
- `counts.orders_matched` and `counts.tracking_found` populated in the JSON report.
- `http_trace_summary.allowed_methods_only` is `true`.
- No customer identifiers or message bodies appear in artifacts.
