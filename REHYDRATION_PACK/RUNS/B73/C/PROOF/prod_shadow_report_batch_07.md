# Prod Shadow Order Status Report

- Run ID: `RUN_20260207_0123Z`
- Generated (UTC): 2026-02-07T01:31:10.160518+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 50
- Tickets scanned: 50
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
- Order-status subset: 23 tickets; 15 matched by order number and 7 matched by email.
- Global order-status rate: 46.0%
- Match rate among order-status: 95.7%
- Tracking present for 20 order-status tickets; ETA available for 2 when no tracking.
- Tracking present rate (matched only): 90.9%; ETA available rate (matched only): 9.1%.
- OpenAI routing calls: 50; OpenAI intent calls: 50.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 50 |
| Classified order status (true) | 23 |
| Classified order status (false) | 27 |
| Order-status rate | 46.0% |
| OpenAI routing called | 50 |
| OpenAI intent called | 50 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 23 |
| Order-status match success | 22 |
| Order-status no match | 1 |
| Match attempted | 23 |
| Matched by order number | 15 |
| Matched by email | 7 |
| Match rate among order-status | 95.7% |
| Tracking present | 20 |
| Tracking rate | 87.0% |
| Tracking present rate (matched only) | 90.9% |
| ETA available when no tracking | 2 |
| ETA rate when no tracking | 66.7% |
| ETA available rate (matched only) | 9.1% |

## Top Failure Modes (Order-status subset)
- missing_email: 1

## Top No-Match Reasons (Order-status subset)
- no_customer_email_on_ticket: 1

## What to Fix Next
- Ensure order number is captured in inbound messages.
- Ensure customer email is available on tickets.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 12

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
