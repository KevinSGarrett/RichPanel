# Test Matrix

**Run ID:** `RUN_20260217_1440Z`  
**Agent:** B  
**Date:** 2026-02-17

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Prod preflight | `python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1440Z/B/preflight_prod.md` |
| CI-equivalent checks | `python scripts/run_ci_checks.py --ci` | fail (uncommitted changes) | `REHYDRATION_PACK/RUNS/RUN_20260217_1440Z/B/run_ci_checks.log` |
| Rehydration pack verification | `python scripts/verify_rehydration_pack.py` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1440Z/B/verify_rehydration_pack.log` |
| Agent prompt freshness | `python scripts/verify_agent_prompts_fresh.py` | pass (override; fingerprint recorded) | `REHYDRATION_PACK/RUNS/RUN_20260217_1440Z/B/verify_agent_prompts_fresh.log` |

## Notes
Pending: re-run `python scripts/run_ci_checks.py --ci` after committing regenerated outputs.
