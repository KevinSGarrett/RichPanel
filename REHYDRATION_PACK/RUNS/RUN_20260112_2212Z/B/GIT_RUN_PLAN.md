# Git Run Plan (Track B idle)

Use this file to coordinate Git/GitHub execution for this run.

**RUN_ID:** RUN_20260112_2212Z  
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
- Allowed paths: not applicable for this idle track
- Locked paths: n/a

---

## Integration checklist (Integrator)
- [x] Pull latest `main`
- [x] Merge agent branches (single branch)
- [x] Run: `python scripts/run_ci_checks.py --ci` (tracked in C)
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
