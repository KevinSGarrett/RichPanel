# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260111_0359Z  
**Mode:** sequential  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260110_1622Z_github_ci_security_stack`  
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
  - n/a (not used in this run)
- Locked paths (do not edit):
  - all

### Agent B
- Allowed paths:
  - `.github/workflows/ci.yml`
  - `docs/08_Engineering/CI_and_Actions_Runbook.md`
  - `REHYDRATION_PACK/RUNS/RUN_20260111_0359Z/**`
- Locked paths:
  - backend/, infra/, other REHYDRATION_PACK run folders

### Agent C
- Allowed paths:
  - integration only (enable auto-merge, branch cleanup)
- Locked paths:
  - same as B unless integration requires otherwise

---

## Integration checklist (Integrator)
- [x] Pull latest `main` (merged via `git merge -X ours origin/main`)
- [ ] Merge agent branches (if parallel) into `run/RUN_20260110_1622Z_github_ci_security_stack`
- [x] Run: `python scripts/run_ci_checks.py --ci` (local)
- [ ] Merge `run/RUN_20260110_1622Z_github_ci_security_stack` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
