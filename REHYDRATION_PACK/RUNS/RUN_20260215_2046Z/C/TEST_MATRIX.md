# Test Matrix

**Run ID:** `RUN_20260215_2046Z`  
**Agent:** C  
**Date:** 2026-02-15

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| PROD preflight | `python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check ...` | pass | `REHYDRATION_PACK/RUNS/RUN_20260215_2046Z/C/preflight_prod.json` |
| PROD shadow eval (read-only) | `python scripts/live_readonly_shadow_eval.py --env prod --allow-deterministic-only --shopify-probe --request-trace --ticket-id ...` | pass | `REHYDRATION_PACK/RUNS/RUN_20260215_2046Z/C/shadow_eval_prod_report.json` |
| CI checks | `python scripts/run_ci_checks.py --ci` | pending | RUN_REPORT output snippet |

## Notes
- All runs executed with read-only/outbound disabled flags.
