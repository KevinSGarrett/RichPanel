# Prod Shadow Order Status Report

- Run ID: `RUN_20260131_1923Z`
- Generated (UTC): 2026-01-31T21:07:23.948238+00:00
- Environment: `prod`
- Classification source: `mixed`
- Classification source counts: openai_intent: 594, deterministic_router: 1
- Tickets scanned: 595
- Conversation mode: `full`

## Env flags
- `MW_ALLOW_NETWORK_READS=true`
- `MW_OPENAI_INTENT_ENABLED=true`
- `MW_OPENAI_ROUTING_ENABLED=true`
- `MW_OPENAI_SHADOW_ENABLED=true`
- `OPENAI_ALLOW_NETWORK=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `SHOPIFY_OUTBOUND_ENABLED=true`
- `SHOPIFY_WRITE_DISABLED=true`

## Executive Summary
- 222 tickets classified as order-status; 0 matched by order number and 0 matched by email.
- Order-status rate: 37.3%
- Tracking present for 0 tickets; ETA available for 0 tickets.
- OpenAI routing calls: 594; OpenAI intent calls: 594.
- Errors: 1

## Stats
| Metric | Count |
| --- | --- |
| Tickets scanned | 595 |
| Classified order status | 222 |
| Order-status rate | 37.3% |
| OpenAI routing called | 594 |
| OpenAI intent called | 594 |
| Shopify lookup forced | 0 |
| Matched by order number | 0 |
| Matched by email | 0 |
| No match | 594 |
| Errors | 1 |
| Tracking present | 0 |
| ETA available | 0 |

## Top Failure Modes
- no_shopify_match: 394
- missing_order_number: 164
- missing_email: 20
- missing_order_number_and_email: 16
- error: 1

## What to Fix Next
- Ensure order number is captured in inbound messages.
- Ensure customer email is available on tickets.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 12

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
