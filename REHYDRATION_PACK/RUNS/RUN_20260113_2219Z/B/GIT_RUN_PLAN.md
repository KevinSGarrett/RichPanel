# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260113_2219Z  
**Mode:** sequential  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260113_2219Z_order_status_pass_strong`  
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
- Allowed paths: n/a (unused this run)
- Locked paths: all

### Agent B
- Allowed paths: backend/src/richpanel_middleware/**, scripts/**, docs/**, REHYDRATION_PACK/RUNS/RUN_20260113_2219Z/**
- Locked paths: infra/, frontend/, non-related generated assets

### Agent C
- Allowed paths: integration only if needed
- Locked paths: same as Agent B unless merging

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/<RUN_ID>`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
