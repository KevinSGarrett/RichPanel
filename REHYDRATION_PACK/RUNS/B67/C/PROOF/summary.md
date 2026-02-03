# B67 Prod Shadow Order Status — Summary

Generated: 2026-02-03 (UTC)

## How to Read These Metrics
- Global stats use **all tickets scanned** as the denominator.
- Order-status subset stats use **only tickets classified as order-status**.

## Green Streak Trend (250 tickets each)
| Run | Run ID | Tickets | Order-status rate | Match rate among order-status | Tracking rate | ETA rate (no tracking) | 429 retries | Warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run1 | `RUN_20260203_0114Z` | 250 | 28.4% | 93.0% | 90.1% | 14.3% | 0 | none |
| run2 | `RUN_20260203_0404Z` | 250 | 30.4% | 93.4% | 88.2% | 33.3% | 0 | none |
| run3 | `RUN_20260203_0400Z` | 250 | 29.2% | 93.2% | 86.3% | 40.0% | 0 | none |

Interpretation:
- All three runs are within the expected band for `order_status_rate` (20%–50%).
- `match_rate_among_order_status` is healthy and stable (>= 85% in all runs).
- No Richpanel 429 retries were observed.
- No token issues were observed (errors = 0 in all runs).

## Top Failure Modes (Order-Status Subset)
Counts are from tickets classified as order-status only:
- run1: `missing_order_number` (3), `missing_email` (2)
- run2: `missing_order_number` (3), `missing_email` (2)
- run3: `missing_order_number` (3), `missing_email` (2)

Actionable takeaways:
- Encourage order number capture in inbound channels.
- Ensure customer email is present on Richpanel tickets.

## Top Failure Modes (Global: All Tickets Scanned)
Counts are across all 250 tickets per run:
- run1: `no_shopify_match` (111), `missing_order_number` (62), `missing_order_number_and_email` (9), `missing_email` (2)
- run2: `no_shopify_match` (107), `missing_order_number` (61), `missing_order_number_and_email` (9), `missing_email` (2)
- run3: `no_shopify_match` (111), `missing_order_number` (60), `missing_order_number_and_email` (9), `missing_email` (2)

Actionable takeaways:
- `no_shopify_match` remains the dominant failure; review Shopify identifiers and linkage rates.
- Missing identifiers remain a consistent contributor; verify order/email extraction paths.
