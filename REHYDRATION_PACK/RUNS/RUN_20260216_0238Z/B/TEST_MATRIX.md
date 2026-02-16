# Test Matrix

**Run ID:** `RUN_20260216_0238Z`  
**Agent:** B  
**Date:** 2026-02-16

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Prod preflight (read-only) | `python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check --out-json REHYDRATION_PACK/RUNS/RUN_20260216_0238Z/B/preflight_prod.json --out-md REHYDRATION_PACK/RUNS/RUN_20260216_0238Z/B/preflight_prod.md` | pass | `REHYDRATION_PACK/RUNS/RUN_20260216_0238Z/B/preflight_prod.md` |
| CI checks | `python scripts/run_ci_checks.py --ci` | pass | `REHYDRATION_PACK/RUNS/RUN_20260216_0238Z/B/RUN_REPORT.md` |

## Notes
CI checks passed with clean-tree regen verification.
