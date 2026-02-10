# B75 — DEV E2E Evidence (PII‑safe)

## AWS / ENV Verification
- `aws sso login --profile rp-admin-dev`
- `aws sts get-caller-identity --profile rp-admin-dev` → **Account** `151124909266`

## Proof Artifact
- `REHYDRATION_PACK/RUNS/B75/B/PROOF/dev_tracking_link_e2e.json`

## Proof Excerpts (from ticket 1356, redacted)
- `meta.env=dev`, `meta.region=us-east-2`, `meta.scenario=order_status`
- `proof_fields.automation_triggered=true`
- `proof_fields.intent_order_status=true`
- `proof_fields.order_matched=true`
- `proof_fields.tracking_number_present=true` (tracking_number_redacted=redacted)
- `proof_fields.reply_contains_tracking_url=true`
- `proof_fields.reply_contains_url_domain=true`
- `proof_fields.reply_url_domain_match=www.fedex.com`
- `proof_fields.latest_comment_is_operator=true`
- `proof_fields.outbound_attempted=true`
- `proof_fields.reply_sent=true`
- `proof_fields.ticket_auto_closed=true`
- `proof_fields.ticket_status=CLOSED`
- `proof_fields.has_loop_prevention_tag=true`
- `proof_fields.carrier_value=FedEx`
- `proof_fields.shipping_method_value=FedEx Ground`
- `proof_fields.shipping_method_matches_carrier=true`
- `tags=[mw-smoke-autoticket, mw-intent-order_status_tracking, mw-routing-applied, mw-auto-replied, mw-order-status-answered, mw-outbound-path-send-message, mw-reply-sent]`

## Code Changes Applied
- `backend/src/richpanel_middleware/automation/delivery_estimate.py` — shipping method normalization + tracking URL fallback
- `backend/src/richpanel_middleware/automation/pipeline.py` — reduced close candidates, ticket snapshot enrichment, operator-reply recheck
- `backend/src/richpanel_middleware/commerce/order_lookup.py` — fulfillment selection fix, empty tracking normalization, ticket snapshot order lookup
- `infra/cdk/lib/richpanel-middleware-stack.ts` — 60s timeout, all runtime flags baked in, Shopify outbound enabled
- `infra/cdk/cdk.json` — DEV allowlist emails + bot author ID

## Deployment/Runtime Fixes Applied
- Deployed DEV stack via local CDK with all runtime flags baked into stack definition.
- Timeout: 60s (was 30s).
- Rate limit: 0.5 RPS (restored from accidental 0.25).
- Close candidates: 3 proven-working payloads (was 22, caused timeout).
- Shopify outbound reads enabled in DEV.
- Bot author ID set via cdk.json context.

## PII Handling
- Ticket/order/tracking identifiers redacted in proof (`redacted` or `redacted:<fingerprint>`).
- No raw emails, order numbers, or tracking numbers stored in proof artifacts.
