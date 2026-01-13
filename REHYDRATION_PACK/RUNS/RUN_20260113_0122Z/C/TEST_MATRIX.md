# Test Matrix

**Run ID:** `RUN_20260113_0122Z`  
**Agent:** C  
**Date:** 2026-01-13

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent suite | `AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python scripts/run_ci_checks.py --ci` | pass | snippet in `C/RUN_REPORT.md` |

## Notes
- Covers numeric tracking test `test_nested_order_tracking_numeric_is_extracted`.
