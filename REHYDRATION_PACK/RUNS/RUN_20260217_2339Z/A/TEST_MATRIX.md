# Test Matrix

**Run ID:** `RUN_20260217_2339Z`  
**Agent:** A  
**Date:** 2026-02-17

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_REPORT.md` |
| Pytest (initial) | `pytest -q` | fail | `REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_REPORT.md` |
| Pytest (with AWS region) | `$env:AWS_REGION="us-east-2"; $env:AWS_DEFAULT_REGION="us-east-2"; pytest -q` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_REPORT.md` |

## Notes
CI checks and pytest passed; pytest required AWS region env vars (1569 tests).
