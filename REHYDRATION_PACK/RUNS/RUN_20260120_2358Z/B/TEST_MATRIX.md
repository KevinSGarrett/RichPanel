# Test Matrix

**Run ID:** `RUN_20260120_2358Z`
**Agent:** B
**Date:** 2026-01-21

| Test | Command | Result | Notes |
| --- | --- | --- | --- |
| CI-equivalent | python scripts/run_ci_checks.py | pass | Local run (warns about legacy run folder names). |
| Pytest | pytest | pass | 281 tests. |
| E2E smoke proof | python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number <redacted> --run-id RUN_20260120_2358Z --scenario order_status_no_tracking_short_window --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2358Z/B/e2e_order_status_no_tracking_short_window_proof.json | pass | PASS_STRONG. |

## Notes
- Proof JSON is PII-safe and includes OpenAI routing + rewrite evidence.
