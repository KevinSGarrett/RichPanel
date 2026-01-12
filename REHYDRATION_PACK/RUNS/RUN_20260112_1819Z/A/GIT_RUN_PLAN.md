# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260112_1819Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260112_1819Z_artifact_closeout`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260112_1819Z_artifact_closeout`

### Parallel (only when scopes are disjoint)
- Agent A: `run/RUN_20260112_1819Z_artifact_closeout-A`
- Agent B: `run/RUN_20260112_1819Z_artifact_closeout-B`
- Agent C: `run/RUN_20260112_1819Z_artifact_closeout-C`
- Integrator merges into `run/RUN_20260112_1819Z_artifact_closeout`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - `REHYDRATION_PACK/RUNS/RUN_20260112_1819Z/A/*`
- Locked paths (do not edit):
  - Any code outside `REHYDRATION_PACK/RUNS/RUN_20260112_1819Z/A/*`

### Agent B
- Allowed paths:
  - None (not participating)
- Locked paths:
  - All paths

### Agent C
- Allowed paths:
  - None (not participating)
- Locked paths:
  - All paths

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260112_1819Z_artifact_closeout`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/RUN_20260112_1819Z_artifact_closeout` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
