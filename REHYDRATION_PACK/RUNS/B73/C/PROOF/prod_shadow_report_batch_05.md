# Prod Shadow Order Status Report

- Run ID: `RUN_20260207_0108Z`
- Generated (UTC): 2026-02-07T01:15:53.164317+00:00
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
- Order-status subset: 15 tickets; 12 matched by order number and 3 matched by email.
- Global order-status rate: 30.0%
- Match rate among order-status: 100.0%
- Tracking present for 14 order-status tickets; ETA available for 1 when no tracking.
- Tracking present rate (matched only): 93.3%; ETA available rate (matched only): 6.7%.
- OpenAI routing calls: 50; OpenAI intent calls: 50.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 50 |
| Classified order status (true) | 15 |
| Classified order status (false) | 35 |
| Order-status rate | 30.0% |
| OpenAI routing called | 50 |
| OpenAI intent called | 50 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 15 |
| Order-status match success | 15 |
| Order-status no match | 0 |
| Match attempted | 15 |
| Matched by order number | 12 |
| Matched by email | 3 |
| Match rate among order-status | 100.0% |
| Tracking present | 14 |
| Tracking rate | 93.3% |
| Tracking present rate (matched only) | 93.3% |
| ETA available when no tracking | 1 |
| ETA rate when no tracking | 100.0% |
| ETA available rate (matched only) | 6.7% |

## Top Failure Modes (Order-status subset)
- None observed in this sample.

## Top No-Match Reasons (Order-status subset)
- None observed in this sample.

## What to Fix Next
- Ensure order number is captured in inbound messages.

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
