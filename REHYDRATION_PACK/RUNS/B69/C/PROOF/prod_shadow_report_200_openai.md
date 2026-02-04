# Prod Shadow Order Status Report (Merged)

- Environment: `prod`
- Tickets scanned: 200
- Order-status rate: 0.45

## Global Stats
- Classified order status (true): 90
- Classified order status (false): 110
- OpenAI routing called: 199
- OpenAI intent called: 199
- Shopify lookup forced: 0
- Richpanel 429 retries: 0

## Order-status Subset
- Order-status count: 90
- Matched by order number: 0
- Matched by email: 0
- Match rate among order-status: 0.0
- Tracking rate: 0.0
- ETA rate when no tracking: 0.0

## Top Failure Modes (Order-status subset)
- no_shopify_match: 59
- missing_order_number: 31

## Batch Sources
- prod_shadow_report_25_openai_batch01.json
- prod_shadow_report_25_openai_batch02.json
- prod_shadow_report_25_openai_batch03.json
- prod_shadow_report_25_openai_batch04.json
- prod_shadow_report_25_openai_batch05.json
- prod_shadow_report_25_openai_batch06.json
- prod_shadow_report_25_openai_batch07.json
- prod_shadow_report_25_openai_batch08.json
