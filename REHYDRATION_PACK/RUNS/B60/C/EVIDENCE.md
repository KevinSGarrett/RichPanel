# Evidence - B60/C

## Workflow run
- URL: https://github.com/KevinSGarrett/RichPanel/actions/runs/21383561925
- Branch: `b60/live-readonly-shadow-metrics`
- Inputs: `sample-size=10`, `shop-domain=scentimen-t.myshopify.com`, `shopify-probe=false`

## Artifacts (downloaded)
- `live-readonly-shadow-eval` (GitHub Actions artifact)
  - `live_readonly_shadow_eval_report_RUN_20260127_0338Z.json`
  - `live_readonly_shadow_eval_summary_RUN_20260127_0338Z.json`
  - `live_readonly_shadow_eval_http_trace_RUN_20260127_0338Z.json`
  - `live_readonly_shadow_eval_report_RUN_20260127_0338Z.md`

## PII-safe summary snippet
```json
{
  "run_id": "RUN_20260127_0338Z",
  "sample_size_requested": 10,
  "tickets_evaluated": 0,
  "order_match_success_count": 0,
  "order_match_failure_count": 0,
  "schema_drift": {"threshold": 0.2, "warning": false},
  "run_warnings": ["ticket_listing_403"],
  "status": "ok"
}
```

## Notes
- Ticket listing endpoints returned 403 in CI; the run continued with `--allow-empty-sample`
  and recorded `run_warnings: ["ticket_listing_403"]`.
- Artifacts are stored under `REHYDRATION_PACK/RUNS/B60/C/PROOF/`.
