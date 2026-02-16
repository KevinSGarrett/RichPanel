# Test Matrix

**Run ID:** `RUN_20260215_2351Z`  
**Agent:** A  
**Date:** 2026-02-15

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent | `python scripts/run_ci_checks.py --ci` | pass | `REHYDRATION_PACK/RUNS/RUN_20260215_2351Z/A/RUN_REPORT.md` |
| Unit tests | `pytest -q` | pass (1534 tests) | `REHYDRATION_PACK/RUNS/RUN_20260215_2351Z/A/RUN_REPORT.md` |

## Notes
Initial `pytest -q` run failed without AWS region; reran with `AWS_REGION=us-east-2` set.
