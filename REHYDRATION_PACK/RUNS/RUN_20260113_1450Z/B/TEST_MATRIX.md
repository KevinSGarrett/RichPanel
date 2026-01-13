# Test Matrix

**Run ID:** RUN_20260113_1450Z  
**Agent:** B  
**Date:** 2026-01-13

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Pipeline + smoke unit tests | `python -m pytest scripts/test_pipeline_handlers.py scripts/test_e2e_smoke_encoding.py` | pass | console output |
| Dev smoke proof (order_status) | `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile richpanel-dev --ticket-number 1035 --run-id RUN_20260113_1450Z --scenario order_status --apply-test-tag` | pass | `REHYDRATION_PACK/RUNS/RUN_20260113_1450Z/B/e2e_outbound_proof.json` |
| CI-equivalent | `python scripts/run_ci_checks.py --ci` | pass | console output (clean tree) |

## Notes
- CI run executed on clean tree; untracked RUN_20260113_1438Z excluded locally to keep git status clean.
