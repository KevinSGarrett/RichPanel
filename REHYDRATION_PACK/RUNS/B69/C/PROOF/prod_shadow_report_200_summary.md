# Prod Shadow Order Status Report Summary (200 tickets)

## Deterministic
- Tickets scanned: 200
- Order-status rate: 0.34
- Match rate among order-status: 0.0
- Tracking rate: 0.0
- ETA rate when no tracking: 0.0

## OpenAI
- Tickets scanned: 200
- Order-status rate: 0.45
- Match rate among order-status: 0.0
- Tracking rate: 0.0
- ETA rate when no tracking: 0.0

## Notes
- Deterministic batches used `--skip-openai-intent`.
- OpenAI batches used `OPENAI_API_KEY` override (Secrets Manager access failed in this environment).
- All batches used SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com.
