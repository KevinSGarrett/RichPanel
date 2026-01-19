# Shopify Strategy Notes (reference)

- Primary secrets: `rp-mw/prod/shopify/admin_api_token` (canonical) and legacy fallback `rp-mw/prod/shopify/access_token`.
- Default shop domain is read from `SHOPIFY_SHOP_DOMAIN`; override when running local tools (e.g., `--shop-domain` in `scripts/live_readonly_shadow_eval.py`).
- Shopify reads are permitted only when `allow_network=True`; writes stay blocked (keep `SHOPIFY_WRITE_DISABLED=true` for read-only validation).
- Order status shadow runs should confirm fields needed by `lookup_order_summary` are present: order id/number, shipping method, tracking number or carrier, created/updated timestamps.
- For store-specific fulfillment quirks, capture findings here and link back from runbooks that consume Shopify data.
