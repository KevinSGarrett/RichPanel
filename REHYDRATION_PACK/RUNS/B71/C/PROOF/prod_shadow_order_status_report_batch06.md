# Prod Shadow Order Status Report

- Run ID: `RUN_20260205_1705Z`
- Generated (UTC): 2026-02-05T17:09:53.728734+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 25
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
- Order-status subset: 5 tickets; 4 matched by order number and 1 matched by email.
- Global order-status rate: 20.0%
- Match rate among order-status: 100.0%
- Tracking present for 4 order-status tickets; ETA available for 1 when no tracking.
- OpenAI routing calls: 25; OpenAI intent calls: 25.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 25 |
| Classified order status (true) | 5 |
| Classified order status (false) | 20 |
| Order-status rate | 20.0% |
| OpenAI routing called | 25 |
| OpenAI intent called | 25 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 5 |
| Match attempted | 5 |
| Matched by order number | 4 |
| Matched by email | 1 |
| Match rate among order-status | 100.0% |
| Tracking present | 4 |
| Tracking rate | 80.0% |
| ETA available when no tracking | 1 |
| ETA rate when no tracking | 100.0% |

## Top Failure Modes (Order-status subset)
- None observed in this sample.

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
