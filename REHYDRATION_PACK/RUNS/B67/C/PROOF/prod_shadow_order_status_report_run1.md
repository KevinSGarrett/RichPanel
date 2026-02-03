# Prod Shadow Order Status Report

- Run ID: `RUN_20260203_0114Z`
- Generated (UTC): 2026-02-03T01:49:55.875958+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 250
- Tickets scanned: 250
- Conversation mode: `full`

## How to Read This Report
- Global stats use all tickets scanned as the denominator.
- Order-status subset stats use only tickets classified as order-status.

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
- Order-status subset: 71 tickets; 49 matched by order number and 17 matched by email.
- Global order-status rate: 28.4%
- Match rate among order-status: 93.0%
- Tracking present for 64 order-status tickets; ETA available for 1 when no tracking.
- OpenAI routing calls: 250; OpenAI intent calls: 250.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 250 |
| Classified order status (true) | 71 |
| Classified order status (false) | 179 |
| Order-status rate | 28.4% |
| OpenAI routing called | 250 |
| OpenAI intent called | 250 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 71 |
| Match attempted | 71 |
| Matched by order number | 49 |
| Matched by email | 17 |
| Match rate among order-status | 93.0% |
| Tracking present | 64 |
| Tracking rate | 90.1% |
| ETA available when no tracking | 1 |
| ETA rate when no tracking | 14.3% |

## Top Failure Modes (Order-status subset)
- missing_order_number: 3
- missing_email: 2

## What to Fix Next
- Ensure order number is captured in inbound messages.
- Ensure customer email is available on tickets.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
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
