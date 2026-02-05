# Prod Shadow Order Status Report

- Run ID: `RUN_20260205_1656Z`
- Generated (UTC): 2026-02-05T17:00:19.954637+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 24
- Tickets scanned: 24
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
- Order-status subset: 17 tickets; 14 matched by order number and 3 matched by email.
- Global order-status rate: 70.8%
- Match rate among order-status: 100.0%
- Tracking present for 14 order-status tickets; ETA available for 3 when no tracking.
- OpenAI routing calls: 24; OpenAI intent calls: 24.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 24 |
| Classified order status (true) | 17 |
| Classified order status (false) | 7 |
| Order-status rate | 70.8% |
| OpenAI routing called | 24 |
| OpenAI intent called | 24 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 17 |
| Match attempted | 17 |
| Matched by order number | 14 |
| Matched by email | 3 |
| Match rate among order-status | 100.0% |
| Tracking present | 14 |
| Tracking rate | 82.4% |
| ETA available when no tracking | 3 |
| ETA rate when no tracking | 100.0% |

## Top Failure Modes (Order-status subset)
- None observed in this sample.

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
