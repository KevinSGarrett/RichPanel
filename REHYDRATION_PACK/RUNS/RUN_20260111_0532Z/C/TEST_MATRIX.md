# Test Matrix

**Run ID:** `RUN_20260111_0532Z`  
**Agent:** C  
**Date:** 2026-01-11

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent | `python scripts/run_ci_checks.py` | pass | RUN_REPORT.md (output) |
| Reply rewrite unit tests | `python scripts/test_llm_reply_rewriter.py` | pass | RUN_REPORT.md |
| Pipeline handlers | `python scripts/test_pipeline_handlers.py` | pass | RUN_REPORT.md |

## Notes
- run_ci_checks includes regen + full validation suite; all green.
