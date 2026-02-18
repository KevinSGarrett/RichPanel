# Test Matrix

**Run ID:** `RUN_20260218_1954Z`  
**Agent:** C  
**Date:** 2026-02-18

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | fail (generated outputs uncommitted) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/RUN_REPORT.md` |
| CDK diff (staging) | `npx cdk diff RichpanelMiddleware-staging` | fail (no AWS creds) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/cdk_diff_staging.txt` |
| CDK diff (prod) | `npx cdk diff RichpanelMiddleware-prod` | fail (no AWS creds) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/cdk_diff_prod.txt` |

## Notes
AWS SSO credentials are required before CDK diffs and deployment verification can proceed.
