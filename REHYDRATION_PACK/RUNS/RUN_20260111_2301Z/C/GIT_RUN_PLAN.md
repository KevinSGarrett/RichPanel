# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260111_2301Z  
**Mode:** sequential (default)  
**Integrator:** C (default; last agent in sequence)  
**Target branch:** `run/RUN_20260111_2301Z_richpanel_outbound_smoke_proof`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260111_2301Z_richpanel_outbound_smoke_proof`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - none (idle)
- Locked paths (do not edit):
  - all

### Agent B
- Allowed paths:
  - scripts/dev_richpanel_outbound_smoke.py
  - REHYDRATION_PACK/RUNS/RUN_20260111_2301Z/B/**
- Locked paths:
  - backend/src/**

### Agent C
- Allowed paths:
  - none (idle)
- Locked paths:
  - all

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260111_2301Z_richpanel_outbound_smoke_proof`
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Merge `run/RUN_20260111_2301Z_richpanel_outbound_smoke_proof` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
