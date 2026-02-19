# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260219_0628Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260219_0628Z`  
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
  - `backend/src/richpanel_middleware/automation/*`
  - `backend/src/richpanel_middleware/commerce/order_lookup.py`
  - `backend/tests/*`
  - `scripts/test_delivery_estimate.py`
  - `scripts/test_pipeline_handlers.py`
  - `scripts/test_live_readonly_shadow_eval.py`
  - `scripts/test_e2e_smoke_encoding.py`
  - `scripts/live_readonly_shadow_eval.py`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260219_0628Z/A/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260219_0628Z/A/evidence/*`
- Locked paths (do not edit):
  - `infra/**`
  - `frontend/**`
  - `backend/src/richpanel_middleware/integrations/**`

### Agent B
- Allowed paths:
  - TBD (Agent B)
- Locked paths:
  - TBD

### Agent C
- Allowed paths:
  - TBD (Agent C)
- Locked paths:
  - TBD

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/<RUN_ID>`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
