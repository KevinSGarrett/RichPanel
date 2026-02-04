# Prod Shadow Order Status Report

- Run ID: `RUN_20260204_0146Z`
- Generated (UTC): 2026-02-04T01:47:34.660393+00:00
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
- Order-status subset: 10 tickets; 0 matched by order number and 0 matched by email.
- Global order-status rate: 40.0%
- Match rate among order-status: 0.0%
- Tracking present for 0 order-status tickets; ETA available for 0 when no tracking.
- OpenAI routing calls: 0; OpenAI intent calls: 0.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 25 |
| Classified order status (true) | 10 |
| Classified order status (false) | 15 |
| Order-status rate | 40.0% |
| OpenAI routing called | 0 |
| OpenAI intent called | 0 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 10 |
| Match attempted | 10 |
| Matched by order number | 0 |
| Matched by email | 0 |
| Match rate among order-status | 0.0% |
| Tracking present | 0 |
| Tracking rate | 0.0% |
| ETA available when no tracking | 0 |
| ETA rate when no tracking | 0.0% |

## Top Failure Modes (Order-status subset)
- no_shopify_match: 6
- missing_order_number: 4

## What to Fix Next
- Ensure order number is captured in inbound messages.

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
