# Test Matrix

**Run ID:** `RUN_20260114_0707Z`  
**Agent:** B  
**Date:** 2026-01-14

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent | `$Env:AWS_REGION="us-east-2"; $Env:AWS_DEFAULT_REGION="us-east-2"; python scripts/run_ci_checks.py --ci` | pass (tests; clean-tree gate requires commit) | excerpts in `RUN_REPORT.md` |

## Notes
- All validations/tests passed; the clean-tree requirement will complete after committing regenerated outputs.
