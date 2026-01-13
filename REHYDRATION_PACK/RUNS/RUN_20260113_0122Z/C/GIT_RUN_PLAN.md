# Git Run Plan

Use this file to coordinate Git/GitHub execution for this run.

**RUN_ID:** RUN_20260113_0122Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/RUN_20260112_2112Z_order_lookup_patch_green`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/<RUN_ID>`

### Parallel (only when scopes are disjoint)
- Agent A: `run/<RUN_ID>-A`
- Agent B: `run/<RUN_ID>-B`
- Agent C: `run/<RUN_ID>-C`
- Integrator merges into `run/<RUN_ID>`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths: none (idle)
- Locked paths: all

### Agent B
- Allowed paths: none (idle)
- Locked paths: all

### Agent C
- Allowed paths:
  - `backend/src/richpanel_middleware/commerce/order_lookup.py`
  - `scripts/test_order_lookup.py`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260113_0122Z/**`
- Locked paths: everything else

---

## Integration checklist (Integrator)
- [x] Pull latest `main`
- [x] Merge agent branches (single branch)
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Merge `run/RUN_20260112_2112Z_order_lookup_patch_green` → `main` (PR #92 auto-merge)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
