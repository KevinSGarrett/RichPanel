# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260114_2025Z  
**Mode:** sequential (docs-only)  
**Integrator:** A (single-agent run)  
**Target branch:** `run/RUN_20260114_2025Z_b39_docs_alignment`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (after merge)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
- Sequential: single branch `run/RUN_20260114_2025Z_b39_docs_alignment`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - `docs/08_Engineering/CI_and_Actions_Runbook.md`
  - `docs/08_Engineering/OpenAI_Model_Plan.md`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260114_2025Z/A/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260114_2025Z/RUN_META.md`
- Locked paths (do not edit):
  - `backend/**`, `infra/**`, any other docs unless required by registry tooling

### Agent B
- Not used (scope is single-agent docs run).

### Agent C
- Not used (scope is single-agent docs run).

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Run: `python scripts/run_ci_checks.py --ci` on a clean tree
- [ ] Create/verify PR #108 (merge commit)
- [ ] Wait for Codecov/patch + Cursor Bugbot green
- [ ] Merge `run/RUN_20260114_2025Z_b39_docs_alignment` → `main`
- [ ] Delete run branch after merge
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md` if required
