# B72 Prod Shadow Order Status â€” Analysis Summary

Scope: 6 batches (50 tickets each), total 300 tickets. Read-only flags enforced; SHOPIFY_SHOP_DOMAIN sourced from prod worker Lambda environment.

## Required metrics (from aggregated JSON stats)
- tickets_scanned: 300
- classified_order_status_true: 113
- order_status_rate: 0.377 (37.7%)
- match_rate: 0.373 (37.3%)
- no_match_rate: 0.627 (62.7%)
- richpanel_429_retry_count: 0

## Evaluation vs expected bands
- Order status rate is **within expected band** (25%â€“55%).
- No-match rate is **high** vs the ideal (<10%). This is a *global* noâ€‘match metric across all tickets (including nonâ€‘orderâ€‘status tickets). It is not limited to the orderâ€‘status subset, so it overstates â€œno matchâ€ vs the orderâ€‘status-only perspective. We should use the orderâ€‘status subset match metrics inside each batch report for a more meaningful Shopifyâ€‘matching view.
- 429 retries are **0**, indicating rate limiting is controlled at current RPS.

## Notable run warnings
- `llm_routing.parse_failed` appeared in batch 3 and batch 6 logs (2 total occurrences). This did not fail the run or block classification; it should be monitored but is not a regression by itself.

## OpenAI classification sanity
- OpenAI routing/intent were enabled for the shadow runs (see report headers). Order status rate is not near the historical 9% bug; it is in normal range.

## Shopify matching sanity
- SHOPIFY_SHOP_DOMAIN was pulled directly from `rp-mw-prod-worker` Lambda env to mirror prod.
- No 401 invalid-token warnings appeared in the re-run batches using the Lambda-sourced domain.

## Conclusion
- Pipeline behavior appears normal for classification rate and rate limiting.
- Global noâ€‘match rate is elevated due to denominator being all tickets; review orderâ€‘status subset match metrics in each batch report for meaningful Shopify matching quality.

Artifacts:
- `REHYDRATION_PACK/RUNS/B72/C/PROOF/prod_shadow_order_status_report_batch_01.json`
- `REHYDRATION_PACK/RUNS/B72/C/PROOF/prod_shadow_order_status_report_batch_02.json`
- `REHYDRATION_PACK/RUNS/B72/C/PROOF/prod_shadow_order_status_report_batch_03.json`
- `REHYDRATION_PACK/RUNS/B72/C/PROOF/prod_shadow_order_status_report_batch_04.json`
- `REHYDRATION_PACK/RUNS/B72/C/PROOF/prod_shadow_order_status_report_batch_05.json`
- `REHYDRATION_PACK/RUNS/B72/C/PROOF/prod_shadow_order_status_report_batch_06.json`
