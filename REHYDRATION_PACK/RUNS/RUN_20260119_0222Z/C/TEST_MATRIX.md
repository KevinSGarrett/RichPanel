# Test Matrix

**Run ID:** `RUN_20260119_0222Z`  
**Agent:** C  
**Date:** 2026-01-19

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent checks | `python scripts/run_ci_checks.py --ci` | fail (regen diffs) | terminal output (see `RUN_REPORT.md`) |

## Notes
- `--ci` fails when regen outputs change; rerun after commit for a clean pass.
