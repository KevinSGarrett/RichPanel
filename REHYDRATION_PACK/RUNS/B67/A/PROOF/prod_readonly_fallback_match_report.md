# Prod Shadow Order Status Report

- Run ID: `RUN_20260202_1611Z`
- Generated (UTC): 2026-02-02T16:23:13.832088+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 74
- Tickets scanned: 74
- Conversation mode: `full`

## Env flags
- `MW_ALLOW_NETWORK_READS=true`
- `MW_OPENAI_INTENT_ENABLED=true`
- `MW_OPENAI_ROUTING_ENABLED=true`
- `MW_OPENAI_SHADOW_ENABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `SHOPIFY_OUTBOUND_ENABLED=true`
- `SHOPIFY_WRITE_DISABLED=true`

## Executive Summary
- 18 tickets classified as order-status; 15 matched by order number and 3 matched by email.
- Order-status rate: 24.3%
- Tracking present for 16 tickets; ETA available for 0 tickets.
- OpenAI routing calls: 74; OpenAI intent calls: 74.
- Errors: 0

## Stats
| Metric | Count |
| --- | --- |
| Tickets scanned | 74 |
| Classified order status | 18 |
| Order-status rate | 24.3% |
| OpenAI routing called | 74 |
| OpenAI intent called | 74 |
| Shopify lookup forced | 0 |
| Matched by order number | 15 |
| Matched by email | 3 |
| No match | 56 |
| Errors | 0 |
| Tracking present | 16 |
| ETA available | 0 |

## Top Failure Modes
- no_shopify_match: 31
- missing_order_number: 16
- missing_email: 6
- missing_order_number_and_email: 3

## What to Fix Next
- Ensure order number is captured in inbound messages.
- Ensure customer email is available on tickets.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
