# B75 — CHANGES

## Code Changes

### `backend/src/richpanel_middleware/automation/delivery_estimate.py`
- Added `normalize_shipping_method_for_carrier()` to align shipping method label with tracking carrier.
- Called in `build_tracking_reply()` before rendering the reply body.
- Sanitized empty tracking numbers (e.g., `[]`) to not render as literal text.

### `backend/src/richpanel_middleware/automation/pipeline.py`
- Reduced close candidates from 22 to 3 proven-working payloads to prevent Lambda timeout.
- Added ticket snapshot enrichment for order lookup when webhook payload lacks order context.
- Added operator-reply recheck before close+tag step.
- Called `normalize_shipping_method_for_carrier()` in the reply context builder.

### `backend/src/richpanel_middleware/commerce/order_lookup.py`
- Fixed fulfillment selection: picks first fulfillment with tracking (not first overall).
- Added `_extract_shopify_fields_best_fulfillment()` helper.
- Normalized empty tracking numbers and carrier values.
- Added `enrich_summary_from_ticket_snapshot()` for ticket-based order lookup.

### `infra/cdk/lib/richpanel-middleware-stack.ts`
- Worker Lambda timeout: 30s → 60s.
- Added all runtime flags to CDK env vars (no longer wiped on deploy).
- Added `RICHPANEL_OUTBOUND_ENABLED`, `SHOPIFY_OUTBOUND_ENABLED`, OpenAI flags, allowlist, bot author ID.
- Rate limit: 0.5 RPS (explicit).

### `infra/cdk/cdk.json`
- Added DEV environment `outboundAllowlistEmails` and `richpanelBotAuthorId`.
