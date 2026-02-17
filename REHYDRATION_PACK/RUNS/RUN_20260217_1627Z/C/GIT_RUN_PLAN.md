# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260217_1627Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260217_1627Z-b88`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260217_1627Z-b88`

### Parallel (only when scopes are disjoint)
- Agent A: `run/<RUN_ID>-A`
- Agent B: `run/<RUN_ID>-B`
- Agent C: `run/<RUN_ID>-C`
- Integrator merges into `run/<RUN_ID>`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - N/A (not used)
- Locked paths (do not edit):
  - N/A

### Agent B
- Allowed paths:
  - N/A (not used)
- Locked paths:
  - N/A

### Agent C
- Allowed paths:
  - `scripts/*`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260217_1627Z/C/*`
- Locked paths:
  - None

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/<RUN_ID>`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
