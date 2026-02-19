# Test Matrix

**Run ID:** `RUN_20260219_0628Z`  
**Agent:** A  
**Date:** 2026-02-19

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| run_ci_checks (CI mode) | `python scripts/run_ci_checks.py --ci` | pass | `REHYDRATION_PACK/RUNS/RUN_20260219_0628Z/A/evidence/run_ci_checks_ci.log` |
| pytest | `pytest -q` | pass | `REHYDRATION_PACK/RUNS/RUN_20260219_0628Z/A/evidence/pytest_q.log` |
| verify_agent_prompts_fresh | `python scripts/verify_agent_prompts_fresh.py` | pass (override) | `REHYDRATION_PACK/RUNS/RUN_20260219_0628Z/A/evidence/verify_agent_prompts_fresh.log` |

## Notes
`run_ci_checks.py --ci` captured via temp log and copied into evidence.
