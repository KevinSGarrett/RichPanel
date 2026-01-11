# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260111_0008Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260111_0008Z` (work performed on `run/RUN_20260110_1622Z_github_ci_security_stack` for CI proof)  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260111_0008Z` (or existing CI branch `run/RUN_20260110_1622Z_github_ci_security_stack`)

### Parallel (only when scopes are disjoint)
- Agent A: `run/RUN_20260111_0008Z-A`
- Agent B: `run/RUN_20260111_0008Z-B`
- Agent C: `run/RUN_20260111_0008Z-C`
- Integrator merges into `run/RUN_20260111_0008Z`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - docs/**
- Locked paths (do not edit):
  - .github/workflows/**
  - codecov.yml

### Agent B
- Allowed paths:
  - .github/workflows/**
  - codecov.yml
  - REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/B/**
- Locked paths:
  - backend/src/** (except the lint cleanup already committed)

### Agent C
- Allowed paths:
  - integration/merge only
- Locked paths:
  - CI workflow unless coordinating with Agent B

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260111_0008Z`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/RUN_20260111_0008Z` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
