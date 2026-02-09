# Prod Shadow Order Status Report

- Run ID: `RUN_20260209_1928Z`
- Generated (UTC): 2026-02-09T19:57:36.905374+00:00
- Environment: `prod`
- Classification source: `openai_intent`
- Classification source counts: openai_intent: 200
- Tickets scanned: 200
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
- Order-status subset: 84 tickets; 57 matched by order number and 26 matched by email.
- Global order-status rate: 42.0%
- Match rate among order-status: 98.8%
- Tracking present for 75 order-status tickets; ETA available for 6 when no tracking.
- Tracking present rate (matched only): 90.4%; ETA available rate (matched only): 7.2%.
- OpenAI routing calls: 200; OpenAI intent calls: 200.
- Errors: 0

## B73 Baseline vs B74 Canary (200)
| Metric | B73 Baseline | B74 Canary | Delta | Status |
| --- | --- | --- | --- | --- |
| order_status_rate | 35.5% | 42.0% | +18.3% | OK |
| match_rate | 91.9% | 98.8% | +7.5% | OK |
| tracking_present_rate | 91.8% | 90.4% | -1.5% | OK |
| eta_available_rate | 6.7% | 7.2% | +7.5% | OK |
| no_match_count | 17 | 1 | -94.1% | OK |
| missing_order_number_count | 189 | 58 | -69.3% | OK |
| richpanel_429_retry_count | 0 | 0 | +0.0% | OK |

**Notes:**
- Status turns **RED** only if a metric regresses by >20% relative vs B73. None regressed.
- Missing-order-number counts are absolute; sample sizes differ (B73=595, B74=200).
- Top Richpanel endpoints (both): `/v1/tickets/number/redacted`, `/v1/conversations/redacted`, `/v1/conversations/redacted/messages`.

## Stats (Global: all tickets scanned)
| Metric | Count |
| --- | --- |
| Tickets scanned | 200 |
| Classified order status (true) | 84 |
| Classified order status (false) | 116 |
| Order-status rate | 42.0% |
| OpenAI routing called | 200 |
| OpenAI intent called | 200 |
| Shopify lookup forced | 0 |
| Richpanel retries (total) | 0 |
| Richpanel 429 retries | 0 |
| Errors | 0 |

## Stats (Order-status subset only)
| Metric | Count |
| --- | --- |
| Order-status count | 84 |
| Order-status match success | 83 |
| Order-status no match | 1 |
| Match attempted | 84 |
| Matched by order number | 57 |
| Matched by email | 26 |
| Match rate among order-status | 98.8% |
| Tracking present | 75 |
| Tracking rate | 89.3% |
| Tracking present rate (matched only) | 90.4% |
| ETA available when no tracking | 6 |
| ETA rate when no tracking | 66.7% |
| ETA available rate (matched only) | 7.2% |

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
- Max requests in any 30s window: 15

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key
