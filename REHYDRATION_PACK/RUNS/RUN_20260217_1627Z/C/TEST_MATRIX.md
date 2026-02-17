# Test Matrix

**Run ID:** `RUN_20260217_1627Z`  
**Agent:** C  
**Date:** 2026-02-17

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | fail (generated docs pending commit) | `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/run_ci_checks.log` |
| Rehydration pack | `python scripts/verify_rehydration_pack.py` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/verify_rehydration_pack.log` |
| Agent prompts | `python scripts/verify_agent_prompts_fresh.py` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/verify_agent_prompts_fresh.log` |
| Pytest | `pytest -q` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/pytest.log` |
| Prod preflight | `python scripts/order_status_preflight_check.py --env prod --aws-profile rp-admin-prod --out-json ... --out-md ...` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/preflight_prod.md` |
| Prod read-only shadow eval | `python scripts/live_readonly_shadow_eval.py --env prod --region us-east-2 --aws-profile rp-admin-prod --openai-shadow-eval --ticket-id [redacted...]` | pass | `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/live_shadow_report.json` |

## Notes
run_ci_checks needs re-run after committing regenerated docs.
