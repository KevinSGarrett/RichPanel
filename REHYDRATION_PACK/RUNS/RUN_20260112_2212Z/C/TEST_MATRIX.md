# Test Matrix

**Run ID:** `RUN_20260112_2212Z`  
**Agent:** C  
**Date:** 2026-01-12

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent suite | `AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python scripts/run_ci_checks.py --ci` | pass | snippet in `C/RUN_REPORT.md` |

## Notes
- Coverage includes new test `test_nested_order_tracking_string_is_extracted`.
- No additional manual tests required for this fix.
