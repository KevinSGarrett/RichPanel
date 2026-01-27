# Evidence - B60/C

## Workflow run
- URL: https://github.com/KevinSGarrett/RichPanel/actions/runs/21385263038
- Branch: `main`
- Inputs: `sample-size=10`, `shop-domain=scentimen-t.myshopify.com`, `shopify-probe=true`
- Ticket IDs: explicit list supplied via workflow input (no listing)

## Artifacts (downloaded)
- `live-readonly-shadow-eval` (GitHub Actions artifact)
  - `live_readonly_shadow_eval_report_RUN_20260127_0505Z.json`
  - `live_readonly_shadow_eval_summary_RUN_20260127_0505Z.json`
  - `live_readonly_shadow_eval_http_trace_RUN_20260127_0505Z.json`
  - `live_readonly_shadow_eval_report_RUN_20260127_0505Z.md`

## PII-safe summary snippet
```json
{
  "run_id": "RUN_20260127_0505Z",
  "sample_size_requested": 17,
  "tickets_evaluated": 17,
  "order_match_success_count": 17,
  "order_match_failure_count": 0,
  "schema_drift": {"threshold": 0.2, "warning": true},
  "run_warnings": [],
  "status": "warning"
}
```

## Notes
- Explicit ticket IDs were passed via workflow input to bypass list endpoint 403s.
- Shopify probe succeeded (`status_code=200`), confirming credentials are valid.
- `schema_drift.warning=true` because >20% of ticket schemas were new in this sample.
- Order match success rate was 100% for this sample (17/17 matched).
- Artifacts are stored under `REHYDRATION_PACK/RUNS/B60/C/PROOF/`.
