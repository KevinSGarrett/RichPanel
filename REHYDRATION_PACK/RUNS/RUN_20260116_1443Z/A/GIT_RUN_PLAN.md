# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260116_1443Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/RUN_20260115_2224Z_newworkflows_docs`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** no for this run  

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
  - None this run
- Locked paths (do not edit):
  - backend/**
  - scripts/**

### Agent B
- Allowed paths:
  - None this run
- Locked paths:
  - backend/**
  - scripts/**

### Agent C
- Allowed paths:
  - backend/**
  - scripts/**
  - docs/**
  - REHYDRATION_PACK/RUNS/RUN_20260116_1443Z/**
- Locked paths:
  - infra/**
  - frontend/**

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (n/a)
- [x] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Merge PR when checks green
- [ ] Confirm Actions are green (Codecov + Bugbot)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
