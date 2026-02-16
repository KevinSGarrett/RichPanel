# B85 PROD Read-Only Assertions

**Run ID:** `RUN_20260216_0343Z`  
**Agent:** C  
**Date (UTC):** 2026-02-16  
**Environment:** prod (us-east-2)

## Evidence files
- `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/prod_runtime_flags_readonly.json`
- `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/preflight_prod.json`
- `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/preflight_prod.md`
- `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/shadow_eval_prod_report.json`
- `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/shadow_eval_prod_summary.md`
- `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/live_shadow_http_trace.json`

## A) No customer contact / no sends
- `would_reply_send` is `false` for all tickets in `shadow_eval_prod_report.json`.

## B) Preorder count + 45-day ship date
- Preorder tickets with Shopify tag matches: 3 (`preorder_tag_matches` contains `pre-order`).
- Ship date validation (order_created_date + 45 calendar days == preorder_ship_date_human):
  - `redacted:cb6d57d9b987` → 2026-01-18 + 45 days = 2026-03-04 (PASS)
  - `redacted:ef6eeba126f7` → 2026-01-17 + 45 days = 2026-03-03 (PASS)
  - `redacted:dbb9295f3e6c` → 2026-01-07 + 45 days = 2026-02-21 (PASS)

## C) “Pre-order Delivery” preorder ticket fixed (key case)
Ticket with Shopify shipping method `Pre-order Delivery` and preorder tag match:
- **Ticket:** `redacted:cb6d57d9b987`
- **Tag detection:** `preorder_tag_matches = ["pre-order"]`
- **Delivery window:** `preorder_window_min_days = 3`, `preorder_window_max_days = 7`
- **delivery_window_human present:** `March 9–March 13, 2026`
- **arrives_in_days present:** `26–30 days`
- **Reply proof signals:**  
  - `draft_reply_has_delivery_window = true`  
  - `draft_reply_has_arrives_in_days = true`  
  - `draft_reply_has_estimated_delivery_phrase = true`

## D) Route distribution sanity (B83 fix)
- Order Status routes > 0 in summary: 9 (81.8%) in `shadow_eval_prod_summary.md`.

## E) No Richpanel writes in HTTP trace
- Parsed `live_shadow_http_trace.json`: Richpanel non-GET requests count = 0.

