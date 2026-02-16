# Test Matrix

**Run ID:** `RUN_20260216_0343Z`  
**Agent:** C  
**Date:** 2026-02-16

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Prod preflight | `python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check --out-json REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/preflight_prod.json --out-md REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/preflight_prod.md` | pass | `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/preflight_prod.md` |
| Prod shadow eval | `python scripts/live_readonly_shadow_eval.py --env prod --region us-east-2 --expect-account-id 878145708918 --allow-deterministic-only --shopify-probe --request-trace --allow-ticket-fetch-failures --ticket-id 116700 --ticket-id 116759 --ticket-id 116762 --ticket-id 116770 --ticket-id 116805 --ticket-id 116837 --ticket-id 116888 --ticket-id 119207 --ticket-id 119201 --ticket-id 119202 --ticket-id 115699 --out REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/shadow_eval_prod_report.json --summary-md-out REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/shadow_eval_prod_summary.md` | pass | `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/shadow_eval_prod_report.json` |
| CI checks | `python scripts/run_ci_checks.py` | pass | `REHYDRATION_PACK/RUNS/RUN_20260216_0343Z/C/RUN_REPORT.md` |

## Notes
Read-only flags enforced for prod checks; CI run captured in RUN_REPORT.
