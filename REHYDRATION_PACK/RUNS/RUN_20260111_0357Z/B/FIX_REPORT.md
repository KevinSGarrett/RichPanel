# Fix Report

**Run ID:** RUN_20260111_0357Z  
**Agent:** B  
**Date:** 2026-01-11

## Fixes applied

| Issue | File(s) | Fix description |
|---|---|---|
| Coverage collecting validation script instead of tests | `.github/workflows/ci.yml` | Changed `coverage run scripts/run_ci_checks.py` to `coverage run -m unittest discover -s scripts -p "test_*.py"` |
| Runbook out of sync with CI | `docs/08_Engineering/CI_and_Actions_Runbook.md` | Updated coverage command references in sections 9 and troubleshooting |
| No lint enforcement plan documented | `docs/08_Engineering/CI_and_Actions_Runbook.md` | Added Section 10 with phased enforcement roadmap |

## Root cause analysis
The CI workflow was running coverage on the validation script (`run_ci_checks.py`) instead of the actual unit tests (`test_*.py`). This meant coverage reports didn't reflect actual test coverage of the codebase.

## Prevention notes
- Runbook section 1 already documented the correct command but ci.yml was inconsistent
- Added explicit coverage verification checklist to runbook section 9
