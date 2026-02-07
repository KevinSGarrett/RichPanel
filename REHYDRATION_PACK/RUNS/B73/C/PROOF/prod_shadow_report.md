# Prod Shadow Order Status Report

- Run ID: `RUN_B73_C_AGGREGATE`
- Generated (UTC): 2026-02-07T02:08:30.114522+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 595
- Tickets scanned: 595
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
- Order-status subset: 211 tickets; 149 matched by order number and 45 matched by email.
- Global order-status rate: 35.5%
- Match rate among order-status: 91.9%
- Tracking present for 178 order-status tickets; ETA available for 13 when no tracking.
- Tracking present rate (matched only): 91.8%; ETA available rate (matched only): 6.7%.
- OpenAI routing calls: 595; OpenAI intent calls: 595.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 595 |
| Classified order status (true) | 211 |
| Classified order status (false) | 384 |
| Order-status rate | 35.5% |
| OpenAI routing called | 595 |
| OpenAI intent called | 595 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 211 |
| Order-status match success | 194 |
| Order-status no match | 17 |
| Match attempted | 211 |
| Matched by order number | 149 |
| Matched by email | 45 |
| Match rate among order-status | 91.9% |
| Tracking present | 178 |
| Tracking rate | 84.4% |
| Tracking present rate (matched only) | 91.8% |
| ETA available when no tracking | 13 |
| ETA rate when no tracking | 39.4% |
| ETA available rate (matched only) | 6.7% |

## Top Failure Modes (Order-status subset)
- missing_order_number: 9
- missing_order_number_and_email: 6
- missing_email: 2

## Top No-Match Reasons (Order-status subset)
- shopify_lookup_0_results: 9
- no_customer_email_on_ticket: 8

## What to Fix Next
- No immediate blockers detected in this sample.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 15

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
