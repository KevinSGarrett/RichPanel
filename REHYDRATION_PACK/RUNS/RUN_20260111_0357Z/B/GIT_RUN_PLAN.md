# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260111_0357Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/RUN_20260110_1622Z_github_ci_security_stack`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/RUN_20260110_1622Z_github_ci_security_stack`

### Parallel (only when scopes are disjoint)
- Not used for this run

---

## Agent scopes and locks (required)

### Agent A
- Scope: Security workflows (codeql, gitleaks, iac_scan, dependabot)
- Status: Complete

### Agent B
- Allowed paths:
  - `.github/workflows/ci.yml`
  - `docs/08_Engineering/CI_and_Actions_Runbook.md`
  - `REHYDRATION_PACK/RUNS/RUN_20260111_0357Z/B/*`
- Locked paths:
  - Security workflow files
  - Other agent run folders

### Agent C
- Scope: Integration and final cleanup
- Status: Pending

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/<RUN_ID>`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
