# Evidence - B60/C

## Workflow run
- URL: https://github.com/KevinSGarrett/RichPanel/actions/runs/21384674820
- Branch: `main`
- Inputs: `sample-size=10`, `shop-domain=scentimen-t.myshopify.com`, `shopify-probe=false`
- Ticket IDs: sourced from `PROD_RICHPANEL_TICKET_IDS` secret (explicit IDs; no listing)

## Artifacts (downloaded)
- `live-readonly-shadow-eval` (GitHub Actions artifact)
  - `live_readonly_shadow_eval_report_RUN_20260127_0434Z.json`
  - `live_readonly_shadow_eval_summary_RUN_20260127_0434Z.json`
  - `live_readonly_shadow_eval_http_trace_RUN_20260127_0434Z.json`
  - `live_readonly_shadow_eval_report_RUN_20260127_0434Z.md`

## PII-safe summary snippet
```json
{
  "run_id": "RUN_20260127_0434Z",
  "sample_size_requested": 17,
  "tickets_evaluated": 17,
  "order_match_success_count": 0,
  "order_match_failure_count": 17,
  "schema_drift": {"threshold": 0.2, "warning": true},
  "run_warnings": [],
  "status": "warning"
}
```

## Notes
- Explicit ticket IDs are provided via `PROD_RICHPANEL_TICKET_IDS` to bypass list endpoint 403s.
- Artifacts are stored under `REHYDRATION_PACK/RUNS/B60/C/PROOF/`.
