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
  - <path patterns>
- Locked paths (do not edit):
  - <path patterns>

### Agent B
- Allowed paths:
  - scripts/dev_richpanel_outbound_smoke.py
  - REHYDRATION_PACK/RUNS/RUN_20260111_2301Z/B/**
- Locked paths:
  - backend/src/** (no code changes beyond script)

### Agent C
- Allowed paths:
  - <path patterns>
- Locked paths:
  - <path patterns>

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260111_2301Z_richpanel_outbound_smoke_proof`
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Merge via PR (merge commit)
- [ ] Confirm Actions green
- [ ] Delete run branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
