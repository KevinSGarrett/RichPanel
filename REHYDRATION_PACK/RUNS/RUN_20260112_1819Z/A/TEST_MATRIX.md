# Test Matrix

**Run ID:** `RUN_20260112_1819Z`  
**Agent:** A  
**Date:** 2026-01-12

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| GPT-5 guard | `python scripts/verify_openai_model_defaults.py` | pass | console output in RUN_REPORT.md |
| CI-equivalent | `python scripts/run_ci_checks.py --ci` | pass | console output in RUN_REPORT.md |

## Notes
- CI-equivalent rerun on clean tree produced a green signal after registries regenerated.
