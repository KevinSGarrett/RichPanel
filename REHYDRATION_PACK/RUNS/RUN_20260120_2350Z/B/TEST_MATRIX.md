# Test Matrix — RUN_20260120_2350Z (Agent B)

## Sandbox E2E Proofs (DEV)

### Order Status — Tracking
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --ticket-number <redacted> --confirm-test-ticket --diagnose-ticket-update --run-id RUN_20260120_2350Z --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`
- **Result:** NOT EXECUTED (dev Richpanel + AWS required)
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`
- **Notes:** Proof JSON includes OpenAI routing + rewrite evidence fields.

### Order Status — No Tracking
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_no_tracking --ticket-number <redacted> --confirm-test-ticket --diagnose-ticket-update --run-id RUN_20260120_2350Z --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json`
- **Result:** NOT EXECUTED (dev Richpanel + AWS required)
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json`
- **Notes:** Proof JSON includes OpenAI routing + rewrite evidence fields.

## Local Checks
- `python scripts/test_e2e_smoke_encoding.py` — PASS
- `python scripts/run_ci_checks.py --ci` — PASS (warnings remain for legacy run folder naming)
