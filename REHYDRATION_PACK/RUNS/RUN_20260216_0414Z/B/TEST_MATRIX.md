# Test Matrix

**Run ID:** `RUN_20260216_0414Z`  
**Agent:** B  
**Date:** 2026-02-16

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Prod preflight | `python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check --out-json REHYDRATION_PACK/RUNS/RUN_20260216_0414Z/B/preflight_prod.json --out-md REHYDRATION_PACK/RUNS/RUN_20260216_0414Z/B/preflight_prod.md` | pass | `REHYDRATION_PACK/RUNS/RUN_20260216_0414Z/B/preflight_prod.md` |
| CI checks | `python scripts/run_ci_checks.py --ci` | pending | `REHYDRATION_PACK/RUNS/RUN_20260216_0414Z/B/RUN_REPORT.md` |

## Notes
Read-only flags enforced for prod preflight; CI checks to be run after artifacts are filled.
