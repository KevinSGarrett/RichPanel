# Prod Shadow Order Status Report (Merged)

- Environment: `prod`
- Tickets scanned: 200
- Order-status rate: 0.34

## Global Stats
- Classified order status (true): 68
- Classified order status (false): 132
- OpenAI routing called: 0
- OpenAI intent called: 0
- Shopify lookup forced: 0
- Richpanel 429 retries: 0

## Order-status Subset
- Order-status count: 68
- Matched by order number: 0
- Matched by email: 0
- Match rate among order-status: 0.0
- Tracking rate: 0.0
- ETA rate when no tracking: 0.0

## Top Failure Modes (Order-status subset)
- no_shopify_match: 38
- missing_order_number: 28
- missing_email: 2

## Batch Sources
- prod_shadow_report_25_deterministic_batch01.json
- prod_shadow_report_25_deterministic_batch02.json
- prod_shadow_report_25_deterministic_batch03.json
- prod_shadow_report_25_deterministic_batch04.json
- prod_shadow_report_25_deterministic_batch05.json
- prod_shadow_report_25_deterministic_batch06.json
- prod_shadow_report_25_deterministic_batch07.json
- prod_shadow_report_25_deterministic_batch08.json
