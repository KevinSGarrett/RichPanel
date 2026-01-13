# Test Matrix

**Run ID:** `RUN_20260113_2219Z`  
**Agent:** B  
**Date:** 2026-01-13

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Dev order_status smoke (diag) | `python scripts/dev_e2e_smoke.py --profile richpanel-dev --env dev --region us-east-2 --scenario order_status --ticket-number 1002 --diagnose-ticket-update --confirm-test-ticket --run-id RUN_20260113_2219Z --wait-seconds 120 --proof-path REHYDRATION_PACK/RUNS/RUN_20260113_2219Z/B/e2e_outbound_proof.json` | PASS_STRONG | `REHYDRATION_PACK/RUNS/RUN_20260113_2219Z/B/e2e_outbound_proof.json` |
| CI equivalence | `python scripts/run_ci_checks.py --ci` | fail (expected until commit of regenerated files) | command output in RUN_REPORT.md (regens succeeded; exit due to uncommitted changes) |

## Notes
- CI suite tests all passed; final rerun after committing regen outputs will be required for exit 0.
