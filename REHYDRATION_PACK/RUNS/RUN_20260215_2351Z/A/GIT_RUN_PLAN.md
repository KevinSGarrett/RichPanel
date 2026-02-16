# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260215_2351Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260215_2351Z`  
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
- Allowed paths:
  - `backend/src/richpanel_middleware/automation/delivery_estimate.py`
  - `backend/tests/test_delivery_estimate_fallback.py`
  - `scripts/live_readonly_shadow_eval.py`
  - `scripts/test_live_readonly_shadow_eval.py`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260215_2351Z/A/*`
- Locked paths (do not edit):
  - None

### Agent B
- Allowed paths:
  - None (not used)
- Locked paths:
  - All other paths

### Agent C
- Allowed paths:
  - None (not used)
- Locked paths:
  - All other paths

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/<RUN_ID>`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
