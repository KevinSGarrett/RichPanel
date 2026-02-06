# Prod Shadow Order Status Report

- Run ID: `RUN_B72_C_AGGREGATE`
- Generated (UTC): 2026-02-06T16:26:34.416987+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 300
- Tickets scanned: 300
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
- Order-status subset: 113 tickets; 82 matched by order number and 30 matched by email.
- Global order-status rate: 37.7%
- Match rate among order-status: 99.1%
- Tracking present for 103 order-status tickets; ETA available for 7 when no tracking.
- OpenAI routing calls: 300; OpenAI intent calls: 300.
- Errors: 0

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 300 |
| Classified order status (true) | 113 |
| Classified order status (false) | 187 |
| Order-status rate | 37.7% |
| OpenAI routing called | 300 |
| OpenAI intent called | 300 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 113 |
| Match attempted | 113 |
| Matched by order number | 82 |
| Matched by email | 30 |
| Match rate among order-status | 99.1% |
| Tracking present | 103 |
| Tracking rate | 91.2% |
| ETA available when no tracking | 7 |
| ETA rate when no tracking | 70.0% |

## Top Failure Modes (Order-status subset)
- missing_email: 1

## What to Fix Next
- Ensure order number is captured in inbound messages.
- Ensure customer email is available on tickets.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Retry Diagnostics
- Total retries: 0
- Status counts: none

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
