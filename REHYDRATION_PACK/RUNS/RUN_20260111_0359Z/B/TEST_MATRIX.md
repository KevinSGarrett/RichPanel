# Test Matrix

**Run ID:** `RUN_20260111_0359Z`  
**Agent:** B  
**Date:** 2026-01-10

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent | `python scripts/run_ci_checks.py --ci` | pass | local console output (all checks green) |
| Coverage unit tests | `coverage run -m unittest discover -s scripts -p "test_*.py"` | pass | local console output; `coverage xml` generated |
| GitHub Actions CI | Workflow run `CI` | pass | https://github.com/KevinSGarrett/RichPanel/actions/runs/20889477918 |

## Notes
- GitHub Actions CI run is green; Codecov patch/project checks succeeded on the same run.
