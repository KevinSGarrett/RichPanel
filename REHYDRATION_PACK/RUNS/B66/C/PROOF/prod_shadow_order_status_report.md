# Prod Shadow Order Status Report

- Run ID: `RUN_20260202_1052Z`
- Generated (UTC): 2026-02-02T11:26:23.545838+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 250
- Tickets scanned: 250
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
- 80 tickets classified as order-status; 58 matched by order number and 17 matched by email.
- Order-status rate: 32.0%
- Tracking present for 71 tickets; ETA available for 3 tickets.
- OpenAI routing calls: 250; OpenAI intent calls: 250.
- Errors: 0

## Match Breakdown (Order-Status Tickets)
- Matched by order number: 58 (72.5%)
- Matched by email: 17 (21.2%)
- No match: 5 (6.2%)

## Tracking & ETA (Matched Orders)
- Matched orders: 75
- Tracking available: 71 (94.7%)
- ETA available: 3 (4.0%)

## Shopify Error Breakdown
- Shopify errors: 0

## Richpanel Retry Diagnostics
- Retries observed: 0
- Retry-After checked: 0; violations: 0

## Match Breakdown (Order-Status Tickets)
- Matched by order number: 58 (72.5%)
- Matched by email: 17 (21.2%)
- No match: 5 (6.2%)

## Tracking & ETA (Matched Orders)
- Matched orders: 75
- Tracking available: 71 (94.7%)
- ETA available: 3 (4.0%)

## Shopify Error Breakdown
- Shopify errors: 0

## Richpanel Retry Diagnostics
- Retries observed: 0
- Retry-After checked: 0; violations: 0

## Stats
| Metric | Count |
| --- | --- |
| Tickets scanned | 250 |
| Classified order status | 80 |
| Order-status rate | 32.0% |
| OpenAI routing called | 250 |
| OpenAI intent called | 250 |
| Shopify lookup forced | 0 |
| Matched by order number | 58 |
| Matched by email | 17 |
| No match | 175 |
| Errors | 0 |
| Tracking present | 71 |
| ETA available | 3 |

## Top Failure Modes
- no_shopify_match: 102
- missing_order_number: 62
- missing_order_number_and_email: 9
- missing_email: 2

## What to Fix Next
- Ensure order number is captured in inbound messages.
- Ensure customer email is available on tickets.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are fully redacted in this run.
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 15

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
