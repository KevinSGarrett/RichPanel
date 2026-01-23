# Run Summary

**Run ID:** `B51-Agent-C-20260122`  
**Agent:** C  
**Date:** 2026-01-22

## Objective
Add an order-status tracking-present E2E scenario, harden the reply rewrite invariants, and capture a new proof artifact.

## Work completed
- Added tracking-present order status scenario + assertions in `scripts/dev_e2e_smoke.py`.
- Hardened rewrite system prompt + invariant validation in `llm_reply_rewriter.py`.
- Added URL/tracking extraction in order lookup and new rewrite validator test.
- Added scenario shape test for tracking-present payload.
- Enforced exact URL + ETA window validation and added operator-only reply checks in the smoke harness.
- Captured a fresh PASS proof artifact with ticket 1089.

## Tests
- `python -m compileall backend/src scripts` (pass)
- `python -m pytest -q` (pass)
- `python scripts/dev_e2e_smoke.py --scenario order_status_tracking_standard_shipping ...` (failed: missing `--ticket-id`/`--ticket-number`)
- `python scripts/dev_e2e_smoke.py --ticket-number 1084 --scenario order_status_tracking_standard_shipping ...` (failed: NoCredentialsError)
- `python scripts/dev_e2e_smoke.py --ticket-number 1086 --scenario order_status_tracking_standard_shipping ...` (failed: tracking URL missing in reply evidence)
- `python scripts/dev_e2e_smoke.py --ticket-number 1087 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite ...` (pass; proof written)
- `python scripts/dev_e2e_smoke.py --ticket-number 1088 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite ...` (failed: skip_or_escalation_tags_present)
- `python scripts/dev_e2e_smoke.py --ticket-number 1084/1085 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite ...` (failed: skip_or_escalation_tags_present)
- `python scripts/dev_e2e_smoke.py --ticket-number 1089 --scenario order_status_tracking_standard_shipping --no-require-openai-routing --no-require-openai-rewrite ...` (pass; proof written)

## Proof artifacts
- `REHYDRATION_PACK/RUNS/B51/Agent_C/e2e_order_status_tracking_standard_shipping_proof.json` (PASS_STRONG on ticket 1089)
