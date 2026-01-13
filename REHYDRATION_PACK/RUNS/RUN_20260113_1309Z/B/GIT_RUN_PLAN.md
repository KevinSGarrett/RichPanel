# Git Run Plan

**RUN_ID:** RUN_20260113_1309Z  
**Mode:** sequential  
**Integrator:** B  
**Target branch:** `run/RUN_20260113_1309Z_order_status_proof_fix_v2`  
**Merge strategy:** merge commit  
**Branch cleanup:** yes (delete run branch after merge)

---

## Main branch rule
- `main` is protected: changes land via PR with required checks.

## Branch plan
- Sequential only for this run; no parallel agent branches.

## Agent scopes and locks

### Agent B (active)
- Allowed paths:
  - `backend/src/richpanel_middleware/**`
  - `scripts/**`
  - `docs/00_Project_Admin/**`
  - `REHYDRATION_PACK/RUNS/RUN_20260113_1309Z/**`
- Locked paths:
  - `infra/**`, `frontend/**`, `*.yaml` under `.github/workflows`

### Agents A/C
- Not used for this run.

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Ensure branch is `run/RUN_20260113_1309Z_order_status_proof_fix_v2`
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Open PR to `main` (merge commit)
- [ ] Confirm Actions, Codecov patch, and Bugbot all green
- [ ] Enable auto-merge and delete branch after merge
- [ ] Update run artifacts with PR links and CI excerpts
