# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260116_0724Z  
**Mode:** sequential  
**Integrator:** B  
**Target branch:** `run/RUN_20260115_2224Z_newworkflows_docs`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** no  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All work performed on: `run/RUN_20260115_2224Z_newworkflows_docs`

### Parallel (only when scopes are disjoint)
- Not used in this run.

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - N/A (no changes)
- Locked paths (do not edit):
  - N/A

### Agent B
- Allowed paths:
  - docs/08_Engineering/CI_and_Actions_Runbook.md
  - docs/_generated/doc_registry.compact.json
  - docs/_generated/doc_registry.json
  - REHYDRATION_PACK/RUNS/RUN_20260116_0724Z/**
- Locked paths:
  - backend/**
  - infra/**
  - scripts/**
  - REHYDRATION_PACK/RUNS/** (other runs)

### Agent C
- Allowed paths:
  - N/A (no changes)
- Locked paths:
  - N/A

---

## Integration checklist (Integrator)
- [ ] Pull latest `main` (not required for existing branch)
- [ ] Merge agent branches (not applicable)
- [x] Run: `python scripts/run_ci_checks.py --ci`
- [x] PR exists for `run/RUN_20260115_2224Z_newworkflows_docs` (https://github.com/KevinSGarrett/RichPanel/pull/112)
- [x] Confirm Actions are green (Codecov + Bugbot green on latest head)
- [ ] Delete run branches + agent branches (not done)
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md` (not done)
