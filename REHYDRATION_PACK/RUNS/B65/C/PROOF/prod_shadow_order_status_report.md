# Prod Shadow Order Status Report

- Run ID: `RUN_20260130_2045Z`
- Generated (UTC): 2026-01-30T20:54:51.937576+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 58
- Tickets scanned: 58
- Conversation mode: `skipped`

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
- 12 tickets classified as order-status; 7 matched by order number and 4 matched by email.
- Order-status rate: 20.7%
- Tracking present for 8 tickets; ETA available for 3 tickets.
- OpenAI routing calls: 58; OpenAI intent calls: 58.
- Errors: 0

## Stats
| Metric | Count |
| --- | --- |
| Tickets scanned | 58 |
| Classified order status | 12 |
| Order-status rate | 20.7% |
| OpenAI routing called | 58 |
| OpenAI intent called | 58 |
| Shopify lookup forced | 0 |
| Matched by order number | 7 |
| Matched by email | 4 |
| No match | 47 |
| Errors | 0 |
| Tracking present | 8 |
| ETA available | 3 |

## Top Failure Modes
- no_shopify_match: 25
- missing_order_number: 22

## What to Fix Next
- Ensure order number is captured in inbound messages.

## Notes
- Ticket identifiers, emails, names, and order numbers are hashed in structured fields.
- Message excerpts are sanitized (HTML stripped; emails/phones/addresses redacted; order numbers may remain).
- No outbound messages are sent; would_auto_reply is theoretical only.

## Richpanel Retry Diagnostics
- Total retries: 24
- Status counts: 429: 24
- /v1/tickets/number/redacted: 24

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 7

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
