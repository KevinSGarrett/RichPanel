# B75 — Agent B (Cursor) — DEV E2E Proof Run Report

## Outcome
- **Status:** PASS — All 7 requirements proven on ticket 1356.
- **Proof artifact:** `REHYDRATION_PACK/RUNS/B75/B/PROOF/dev_tracking_link_e2e.json`

## What was proved (ticket 1356)
| # | Requirement | Result |
|---|-------------|--------|
| 1 | Automation triggers | ✅ `automation_triggered=true` |
| 2 | Intent = order status | ✅ `intent_order_status=true` (tag `mw-intent-order_status_tracking`) |
| 3 | Order matched | ✅ `order_matched=true` (carrier=FedEx) |
| 4 | Tracking number present | ✅ `tracking_number_present=true` (redacted) |
| 5 | Tracking LINK present (carrier domain) | ✅ `reply_url_domain_match=www.fedex.com` |
| 6 | Operator reply path (/send-message) | ✅ `latest_comment_is_operator=true`, tag `mw-outbound-path-send-message` |
| 7 | Ticket auto-closed | ✅ `ticket_status=CLOSED`, tag `mw-auto-replied` |

## What was done
1. **Normalized shipping method labels** based on tracking carrier (`normalize_shipping_method_for_carrier`).
2. **Enabled Shopify outbound reads** in DEV worker so tracking numbers are pulled from Shopify fulfillments.
3. **Fixed fulfillment selection** to pick the first fulfillment with tracking (not the first fulfillment overall).
4. **Fixed empty tracking number rendering** (`[]` no longer rendered as literal text).
5. **Fixed auto-close** by reducing close candidates to 3 proven-working payloads (was 22, causing timeout).
6. **Baked all runtime flags into CDK stack** so deploys no longer wipe env vars.
7. **Set Lambda timeout to 60s** in CDK (was 30s, caused worker to time out before close step).
8. **Restored Richpanel rate limit to 0.5 RPS** (was accidentally lowered to 0.25).

## Key proof fields (PII‑safe)
- `automation_triggered=true`
- `intent_order_status=true`
- `order_matched=true`
- `tracking_number_present=true` (redacted)
- `reply_contains_url_domain=true` with `reply_url_domain_match=www.fedex.com`
- `latest_comment_is_operator=true`
- `outbound_attempted=true`
- `reply_sent=true`
- `ticket_auto_closed=true` with `ticket_status=CLOSED`
- `has_loop_prevention_tag=true` (`mw-auto-replied`)
- `shipping_method_value=FedEx Ground` (normalized from `USPS/UPS® Ground`)

## Notes
- Ticket auto-closes by design after middleware sends reply.
- Follow-up customer replies route to Email Support Team via `mw-auto-replied` loop prevention tag.
- Order 1106830 has no fulfillment tracking in Shopify (0 fulfillments) — this is a data issue, not a middleware issue.
