# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260218_1442Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260218_1442Z`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260218_1442Z`

### Parallel (only when scopes are disjoint)
- Agent A: `run/RUN_20260218_1442Z-A`
- Agent B: `run/RUN_20260218_1442Z-B`
- Agent C: `run/RUN_20260218_1442Z-C`
- Integrator merges into `run/RUN_20260218_1442Z`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - none (not assigned)
- Locked paths (do not edit):
  - NONE

### Agent B
- Allowed paths:
  - backend/src/richpanel_middleware/automation/delivery_estimate.py
  - backend/src/richpanel_middleware/automation/order_status_prompts.py
  - backend/src/richpanel_middleware/automation/pipeline.py
  - backend/tests/test_delivery_estimate_fallback.py
  - backend/tests/test_order_status_reply_personalization.py
  - scripts/test_delivery_estimate.py
  - docs/00_Project_Admin/Progress_Log.md
  - docs/_generated/*
  - REHYDRATION_PACK/RUNS/RUN_20260218_1442Z/B/*
- Locked paths:
  - NONE

### Agent C
- Allowed paths:
  - (integrator only)
- Locked paths:
  - NONE

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260218_1442Z`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/RUN_20260218_1442Z` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
