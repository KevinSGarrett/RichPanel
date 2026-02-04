# Prod Shadow Order Status Report

- Run ID: `RUN_20260204_0056Z`
- Generated (UTC): 2026-02-04T00:57:14.508396+00:00
- Environment: `prod`
- Classification source: `deterministic_router`
- Classification source counts: deterministic_router: 25
- Tickets scanned: 25
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
- Order-status subset: 9 tickets; 0 matched by order number and 0 matched by email.
- Global order-status rate: 36.0%
- Match rate among order-status: 0.0%
- Tracking present for 0 order-status tickets; ETA available for 0 when no tracking.
- OpenAI routing calls: 0; OpenAI intent calls: 0.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 25 |
| Classified order status (true) | 9 |
| Classified order status (false) | 16 |
| Order-status rate | 36.0% |
| OpenAI routing called | 0 |
| OpenAI intent called | 0 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 9 |
| Match attempted | 9 |
| Matched by order number | 0 |
| Matched by email | 0 |
| Match rate among order-status | 0.0% |
| Tracking present | 0 |
| Tracking rate | 0.0% |
| ETA available when no tracking | 0 |
| ETA rate when no tracking | 0.0% |

## Top Failure Modes (Order-status subset)
- missing_order_number: 4
- no_shopify_match: 4
- missing_email: 1

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
