# Test Matrix

**Run ID:** `RUN_20260219_1524Z`  
**Agent:** B  
**Date:** 2026-02-19

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | pass | `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/run_ci_checks_ci.log` |
| Pytest | `pytest -q` | pass | `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/pytest_q.log` |
| Rehydration pack verify | `python scripts/verify_rehydration_pack.py` | pass | `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/verify_rehydration_pack.log` |
| Prompt freshness | `python scripts/verify_agent_prompts_fresh.py` | pass (override) | `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/verify_agent_prompts_fresh.log` |
| Prompt fingerprint | `python -c "from scripts.verify_agent_prompts_fresh import prompt_set_fingerprint, CURRENT_PROMPTS_PATH; ..."` | pass | `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/prompt_fingerprint.log` |

## Notes
Prompt repeat override is active; fingerprint captured via direct helper call.
