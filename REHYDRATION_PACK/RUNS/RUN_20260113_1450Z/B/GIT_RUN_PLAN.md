# Git Run Plan

Use this file to coordinate Git/GitHub execution for this repair run.

**RUN_ID:** RUN_20260113_1450Z  
**Mode:** sequential  
**Integrator:** B  
**Target branch:** `run/RUN_20260113_1450Z_order_status_repair_loop_prevention`  
**Merge strategy:** merge commit (required)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: land changes via PR with merge commit (no squash).

## Branch plan
- Single branch owned by Agent B: `run/RUN_20260113_1450Z_order_status_repair_loop_prevention`.

## Agent scopes and locks
### Agent B
- Allowed: `backend/src/richpanel_middleware/automation/pipeline.py`, `scripts/dev_e2e_smoke.py`, `scripts/test_*`, `docs/08_Engineering/CI_and_Actions_Runbook.md`, `REHYDRATION_PACK/RUNS/RUN_20260113_1450Z/B/**`.
- Locked: all other paths unless coordinated.

### Agents A/C
- Not active this run; no edits planned.

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Ensure Codecov patch + Bugbot green on PR
- [ ] Run: `python scripts/run_ci_checks.py --ci` on clean tree
- [ ] Merge PR with merge commit and delete branch
- [ ] Update run artifacts and `REHYDRATION_PACK/GITHUB_STATE.md`
