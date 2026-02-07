# Prod Shadow Order Status Report

- Run ID: `RUN_20260207_0200Z`
- Generated (UTC): 2026-02-07T02:07:07.369860+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 45
- Tickets scanned: 45
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
- Order-status subset: 13 tickets; 11 matched by order number and 1 matched by email.
- Global order-status rate: 28.9%
- Match rate among order-status: 92.3%
- Tracking present for 11 order-status tickets; ETA available for 1 when no tracking.
- Tracking present rate (matched only): 91.7%; ETA available rate (matched only): 8.3%.
- OpenAI routing calls: 45; OpenAI intent calls: 45.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 45 |
| Classified order status (true) | 13 |
| Classified order status (false) | 32 |
| Order-status rate | 28.9% |
| OpenAI routing called | 45 |
| OpenAI intent called | 45 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 13 |
| Order-status match success | 12 |
| Order-status no match | 1 |
| Match attempted | 13 |
| Matched by order number | 11 |
| Matched by email | 1 |
| Match rate among order-status | 92.3% |
| Tracking present | 11 |
| Tracking rate | 84.6% |
| Tracking present rate (matched only) | 91.7% |
| ETA available when no tracking | 1 |
| ETA rate when no tracking | 50.0% |
| ETA available rate (matched only) | 8.3% |

## Top Failure Modes (Order-status subset)
- missing_order_number_and_email: 1

## Top No-Match Reasons (Order-status subset)
- no_customer_email_on_ticket: 1

## What to Fix Next
- Ensure order number is captured in inbound messages.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 13

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
