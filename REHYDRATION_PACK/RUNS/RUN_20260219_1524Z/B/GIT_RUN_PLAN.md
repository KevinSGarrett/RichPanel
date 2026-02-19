# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260219_1524Z  
**Mode:** parallel  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260219_1524Z`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260219_1524Z`

### Parallel (only when scopes are disjoint)
- Agent A: `run/RUN_20260219_1524Z-A`
- Agent B: `run/RUN_20260219_1524Z-B93B`
- Agent C: `run/RUN_20260219_1524Z-C`
- Integrator merges into `run/RUN_20260219_1524Z`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/A/**`
- Locked paths (do not edit):
  - `infra/cdk/**`

### Agent B
- Allowed paths:
  - `backend/src/richpanel_middleware/automation/**`
  - `backend/tests/test_reply_rewrite_validation.py`
  - `backend/tests/test_order_status_reply_personalization.py`
  - `scripts/test_llm_reply_rewriter.py`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/**`
  - `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/**`
- Locked paths:
  - `infra/cdk/**`
  - `reference/**`

### Agent C
- Allowed paths:
  - `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/C/**`
- Locked paths:
  - `infra/cdk/**`

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260219_1524Z`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/RUN_20260219_1524Z` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
