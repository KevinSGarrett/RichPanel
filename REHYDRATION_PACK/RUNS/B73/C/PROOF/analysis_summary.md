# B73 Prod Shadow Order Status - Analysis Summary

Scope: 12 batches, 595 tickets total (50 per batch).

## Required metrics (order-status conditioned)
- tickets_scanned: 595
- order_status_true: 211
- order_status_false: 384
- order_status_rate: 0.355
- order_status_match_rate: 0.919
- tracking_present_rate (matched only): 0.918
- eta_available_rate (matched only): 0.067

## No-match reasons (order-status subset, top)
- shopify_lookup_0_results: 9
- no_customer_email_on_ticket: 8

## Rate limiting + retries
- Richpanel retries (total): 0
- Richpanel 429 retries: 0
- Max requests in any 30s window: 15

Artifacts:
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.md`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/run_meta.json`
