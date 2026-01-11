# Git Run Plan

**RUN_ID:** RUN_20260111_0532Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/B32_llm_reply_rewrite_20260110` (PR #72)  
**Merge strategy:** merge commit  
**Branch cleanup:** yes after auto-merge

---

## Main branch rule
- `main` protected; land via PR with green checks.

## Branch plan
- Work directly on `run/B32_llm_reply_rewrite_20260110`; no parallel branches.

## Agent scopes and locks
- Allowed: backend middleware + lambda worker, scripts, REHYDRATION_PACK/RUNS/**
- Locked: secrets/infra/frontend assets.

## Integration checklist
- [ ] Rebase/merge latest `main`
- [ ] Run `python scripts/run_ci_checks.py`
- [ ] Push branch and enable auto-merge (merge commit)
- [ ] Update run artifacts + Progress_Log.md
