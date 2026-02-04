# Prod Shadow Order Status Report

- Run ID: `RUN_20260204_0051Z`
- Generated (UTC): 2026-02-04T00:51:17.396435+00:00
- Environment: `prod`
- Classification source: `deterministic_router`
- Classification source counts: deterministic_router: 3
- Tickets scanned: 3
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
- Order-status subset: 0 tickets; 0 matched by order number and 0 matched by email.
- Global order-status rate: 0.0%
- Match rate among order-status: n/a
- Tracking present for 0 order-status tickets; ETA available for 0 when no tracking.
- OpenAI routing calls: 0; OpenAI intent calls: 0.
- Errors: 3

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 3 |
| Classified order status (true) | 0 |
| Classified order status (false) | 3 |
| Order-status rate | 0.0% |
| OpenAI routing called | 0 |
| OpenAI intent called | 0 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 3 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 0 |
| Match attempted | 0 |
| Matched by order number | 0 |
| Matched by email | 0 |
| Match rate among order-status | n/a |
| Tracking present | 0 |
| Tracking rate | n/a |
| ETA available when no tracking | 0 |
| ETA rate when no tracking | n/a |

## Top Failure Modes (Order-status subset)
- None observed in this sample.

## What to Fix Next
- No immediate blockers detected in this sample.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: None
- api_key_secret_id: rp-mw/prod/richpanel/api_key
