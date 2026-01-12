# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260112_1444Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/RUN_20260112_1444Z_worker_flag_cov`  
**Merge strategy:** merge commit  
**Branch cleanup:** yes  

---

## Main branch rule
- `main` is protected: changes land via PR with required checks; merge commit only.

## Branch plan
- Single branch: `run/RUN_20260112_1444Z_worker_flag_cov`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - none (idle)
- Locked paths (do not edit):
  - backend/**
  - REHYDRATION_PACK/**

### Agent B
- Allowed paths:
  - none (idle)
- Locked paths:
  - backend/**
  - REHYDRATION_PACK/**

### Agent C
- Allowed paths:
  - scripts/test_worker_handler_flag_wiring.py
  - REHYDRATION_PACK/RUNS/RUN_20260112_1444Z/**
- Locked paths:
  - infra/**
  - unrelated backend modules

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Rebase/merge to keep branch current
- [ ] Run: `AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python scripts/run_ci_checks.py --ci`
- [ ] Open PR and confirm Codecov patch/project green
- [ ] Trigger Bugbot review (`bugbot run` comment)
- [ ] Merge via merge commit after green checks
- [ ] Delete run branches after merge
- [ ] Update REHYDRATION_PACK/GITHUB_STATE.md if required
