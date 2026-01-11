# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260111_0504Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `pr72-fix` (tracking `origin/run/B32_llm_reply_rewrite_20260110`)  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (delete feature branch after merge)

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All work on `pr72-fix` then raise PR #72 to `main`.

### Parallel (not used this run)
- N/A

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - docs/, REHYDRATION_PACK/
- Locked paths (do not edit):
  - backend/src/**

### Agent B
- Allowed paths:
  - infra/, scripts/verify_* , docs/
- Locked paths:
  - backend/src/**

### Agent C
- Allowed paths:
  - backend/src/richpanel_middleware/**
  - scripts/**
  - config/.env.example
  - REHYDRATION_PACK/RUNS/RUN_20260111_0504Z/C/**
- Locked paths:
  - infra/cdk/**

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Rebase/merge PR #72 branch with latest `main`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Enable auto-merge on PR #72 and wait for green checks
- [ ] Merge PR #72 → `main` (merge commit)
- [ ] Delete feature branch after merge
- [ ] Update run artifacts and GITHUB_STATE if required
