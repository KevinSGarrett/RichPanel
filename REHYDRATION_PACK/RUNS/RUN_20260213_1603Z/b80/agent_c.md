# B80 Agent C Run Notes

## AWS Identity

- Account: 878145708918

## Status

- Preflight run completed (PASS with refresh-lambda check skipped).
- Shadow eval run completed (OpenAI intent enabled); preorder_proof emitted for 2 non-preorder tickets.
- Ticket 116700 diagnosis captured (see below); preorder-positive proof still pending.
- Tests + CI executed.

## Preflight (PROD)

- Command: `python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check --out-json REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/preflight_prod.json --out-md REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/preflight_prod.md`
- Result: `overall_status=PASS`
- Note: refresh Lambda last-success check skipped; token refresh is not required for read-only proof runs.

## Tests

- `python -m unittest scripts.test_live_readonly_shadow_eval` (PASS)
- `python scripts/run_ci_checks.py --ci` (FAIL: generated docs changed after regen; expected new run entry + runbook update)
- `python -m unittest scripts.test_live_readonly_shadow_eval` (PASS with MW_ENV=dev; SHOPIFY_SHOP_DOMAIN=test-shop.myshopify.com)
- `python scripts/run_ci_checks.py --ci` (PASS in prod env with read-only flags + SHOPIFY_SHOP_DOMAIN set)

## Shadow Eval (PROD, read-only)

- Command: `MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true OPENAI_ALLOW_NETWORK=true python scripts/live_readonly_shadow_eval.py --env prod --region us-east-2 --expect-account-id 878145708918 --allow-deterministic-only --shopify-probe --request-trace --allow-ticket-fetch-failures --ticket-id 116700 --ticket-id 116759 --ticket-id 116762 --ticket-id 116770 --ticket-id 116805 --ticket-id 116837 --ticket-id 116888 --out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_report.json --summary-md-out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_summary.md`
- Summary (RUN_20260213_1729Z): tickets_scanned=7; orders_matched=7; tracking_found=7; eta_available=7; would_reply_send=false for all tickets
- preorder_proof present for all 7 tickets; preorder_delivery_estimate=true for ticket 116837 (redacted:cb6d57d9b987)
- Ticket 116700 now classified as order_status_tracking via OpenAI override after subject+comment concatenation in shadow eval.
- Preorder-tag summary added to `shadow_eval_prod_summary.md` (PII-safe, redacted ticket IDs).
- Combined preorder total across additional tests: 3 preorder matches (119207, 119201, 116837) across the 7-ticket run + 4-ticket run.

## Shadow Eval (PROD, read-only) — Ticket 119207

- Command: `MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true OPENAI_ALLOW_NETWORK=true python scripts/live_readonly_shadow_eval.py --env prod --region us-east-2 --expect-account-id 878145708918 --allow-deterministic-only --shopify-probe --request-trace --allow-ticket-fetch-failures --ticket-id 119207 --out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_report_119207.json --summary-md-out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_summary_119207.md`
- Result (RUN_20260213_1955Z): order_status_candidate=true; routing_intent=order_status_tracking
- preorder_delivery_estimate=true with all required draft reply signals present (pre-order wording, ship date, ship-in-days, delivery window, arrives-in-days, tracking line)
- would_reply_send=false

## Shadow Eval (PROD, read-only) — Tickets 119207/119201/119202/115699

- Command: `MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true OPENAI_ALLOW_NETWORK=true python scripts/live_readonly_shadow_eval.py --env prod --region us-east-2 --expect-account-id 878145708918 --allow-deterministic-only --shopify-probe --request-trace --allow-ticket-fetch-failures --ticket-id 119207 --ticket-id 119201 --ticket-id 119202 --ticket-id 115699 --out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_report_4tickets.json --summary-md-out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_summary_4tickets.md`
- Result (RUN_20260213_2103Z):

- 119207: order_status_tracking; preorder_delivery_estimate=true; all preorder draft signals present; would_reply_send=false
- 119201: order_status_tracking; preorder_delivery_estimate=true; all preorder draft signals present; would_reply_send=false
- 119202: routing_intent=billing_issue; order_status_candidate=false; no preorder_proof; would_reply_send=false
- 115699: routing_intent=unknown_other; order_status_candidate=false; no preorder_proof; would_reply_send=false

## PR

- PR: `https://github.com/KevinSGarrett/RichPanel/pull/249`
- Labels: risk:R1, gate:claude
- @cursor review triggered; checks in progress at time of note.

## Ticket 116700 diagnosis (PII-safe)

- Shadow eval now classifies as order_status_tracking (OpenAI override) after subject+comment concatenation in shadow eval input.
- Extracted order number matches order `#1213333` (not `#1214238`), so preorder tags are not expected for 116700 in the current ticket payload.
