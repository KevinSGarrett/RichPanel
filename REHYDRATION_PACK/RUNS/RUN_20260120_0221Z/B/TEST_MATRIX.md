# Test Matrix — RUN_20260120_0221Z (Agent B)

## Sandbox E2E Proofs (DEV)

### Order Status — No Tracking (Short Window)
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_no_tracking_short_window --ticket-number <redacted> --send-followup --run-id RUN_20260120_0221Z --wait-seconds 120 --json-out REHYDRATION_PACK/RUNS/RUN_20260120_0221Z/B/order_status_no_tracking_short_window.json`
- **Result:** PASS_STRONG
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_0221Z/B/order_status_no_tracking_short_window.json`
- **Notes:** Ticket closed by middleware; follow-up routed to support; no auto-reply on follow-up.

### Order Status — Tracking
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --ticket-number <redacted> --send-followup --run-id RUN_20260120_0221Z --wait-seconds 120 --json-out REHYDRATION_PACK/RUNS/RUN_20260120_0221Z/B/order_status_tracking.json`
- **Result:** PASS_STRONG
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_0221Z/B/order_status_tracking.json`
- **Notes:** Ticket closed by middleware; follow-up routed to support; no auto-reply on follow-up.

## Local Checks
- `python scripts/test_pipeline_handlers.py` — PASS
- `python -m unittest scripts.test_e2e_smoke_encoding` — PASS
- `python scripts/run_ci_checks.py --ci` — FAIL (generated files changed after regen; legacy run folder warnings)
