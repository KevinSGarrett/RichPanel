# Test Matrix — RUN_20260120_2350Z (Agent B)

## Sandbox E2E Proofs (DEV)

### Order Status — Tracking
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1075 --run-id RUN_20260120_2350Z --scenario order_status_tracking --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`
- **Result:** PASS_STRONG
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`
- **Notes:** OpenAI routing + rewrite evidence captured; fallback accepted when rewrite output is suppressed.

### Order Status — No Tracking
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1076 --run-id RUN_20260120_2350Z --scenario order_status_no_tracking --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json`
- **Result:** PASS_STRONG
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json`
- **Notes:** OpenAI routing + rewrite evidence captured; fallback accepted when rewrite output is suppressed.

## Local Checks
- `python scripts/test_openai_client.py` — PASS
- `python scripts/test_llm_reply_rewriter.py` — PASS
- `python scripts/test_llm_routing.py` — PASS
- `python scripts/test_e2e_smoke_encoding.py` — PASS
- `python scripts/run_ci_checks.py --ci` — PASS (warnings remain for legacy run folder naming)
