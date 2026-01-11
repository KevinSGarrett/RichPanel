# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260111_0008Z  
**Mode:** build (sequential)  
**Integrator:** C  
**Target branch:** `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (delete after merge)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All work on: `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`

### Parallel (only when scopes are disjoint)
- Not used this run.

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - n/a (single-agent run)
- Locked paths (do not edit):
  - n/a

### Agent B
- Allowed paths:
  - n/a (single-agent run)
- Locked paths:
  - n/a

### Agent C
- Allowed paths:
  - `backend/src/richpanel_middleware/automation/*`
  - `backend/src/richpanel_middleware/integrations/richpanel/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/C/*`
- Locked paths:
  - `infra/`, `frontend/` (out of scope)

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`
- [x] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/B33_ticketmetadata_shadow_fix_and_gpt5_models` → `main` (via PR)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
