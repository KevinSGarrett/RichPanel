# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260216_2005Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260216_2005Z`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260216_2005Z`

### Parallel (only when scopes are disjoint)
- Agent A: `run/RUN_20260216_2005Z-A`
- Agent B: `run/RUN_20260216_2005Z-B`
- Agent C: `run/RUN_20260216_2005Z-C`
- Integrator merges into `run/RUN_20260216_2005Z`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - `backend/src/richpanel_middleware/automation/delivery_estimate.py`
  - `backend/tests/test_delivery_estimate_fallback.py`
  - `scripts/*`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260216_2005Z/A/*`
- Locked paths (do not edit):
  - AWS/CDK/SSM/Secrets Manager configs
  - Production deploy workflows

### Agent B
- Allowed paths:
  - N/A
- Locked paths:
  - N/A

### Agent C
- Allowed paths:
  - N/A
- Locked paths:
  - N/A

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260216_2005Z`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/RUN_20260216_2005Z` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
