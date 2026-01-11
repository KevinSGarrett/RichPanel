# Git Run Plan

**RUN_ID:** RUN_20260111_0512Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/B32_llm_reply_rewrite_20260110` (PR #72)  
**Merge strategy:** merge commit (default)  
**Branch cleanup:** yes after PR auto-merge/delete

---

## Main branch rule
- `main` is protected: land via PR with green checks.

## Branch plan
- Work directly on `run/B32_llm_reply_rewrite_20260110` (no parallel agents).

## Agent scope/locks
- Allowed: `backend/src/richpanel_middleware/**`, `backend/src/lambda_handlers/worker/**`, `scripts/**`, `REHYDRATION_PACK/RUNS/RUN_20260111_0512Z/**`.
- Locked: secrets, infra, frontend.

## Integration checklist
- [ ] Pull latest `main`
- [ ] Keep branch up to date (rebase/merge as needed)
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Update PR #72 summary; request review; enable auto-merge; delete branch post-merge
- [ ] Record outcomes in RUN_REPORT.md
