# Git Run Plan

Use this file to coordinate Git/GitHub execution for this run.

**RUN_ID:** RUN_20260113_1450Z  
**Mode:** sequential  
**Integrator:** B  
**Target branch:** `run/RUN_20260113_1450Z_order_status_repair_loop_prevention`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes  

---

## Main branch rule
- `main` is protected: merge via PR with merge commit only.

## Branch plan
- Agent C inactive for this run; no branch work.

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - n/a
- Locked paths (do not edit):
  - all

### Agent B
- Allowed paths:
  - see Agent B plan file
- Locked paths:
  - n/a for Agent C

### Agent C
- Allowed paths:
  - none (inactive)
- Locked paths:
  - all

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/RUN_20260113_1450Z_order_status_repair_loop_prevention`
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Merge `run/<RUN_ID>` → `main` with merge commit
- [ ] Confirm Actions are green
- [ ] Delete run branches after merge
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
