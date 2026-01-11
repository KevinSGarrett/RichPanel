# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260110_1638Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (default)
- All agents use: `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`

### Parallel (only when scopes are disjoint)
- Agent A: `run/B33_ticketmetadata_shadow_fix_and_gpt5_models-A`
- Agent B: `run/B33_ticketmetadata_shadow_fix_and_gpt5_models-B`
- Agent C: `run/B33_ticketmetadata_shadow_fix_and_gpt5_models-C`
- Integrator merges into `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - n/a (not active this run)
- Locked paths (do not edit):
  - n/a

### Agent B
- Allowed paths:
  - n/a (not active this run)
- Locked paths:
  - n/a

### Agent C
- Allowed paths:
  - backend/src/richpanel_middleware/automation/**
  - scripts/test_openai_client.py
  - config/.env.example
  - REHYDRATION_PACK/RUNS/RUN_20260110_1638Z/C/**
- Locked paths:
  - docs/_generated/**
  - reference/_generated/**

---

## Integration checklist (Integrator)
- [ ] Pull latest `main` (branch cut from current HEAD)
- [ ] Merge agent branches (if parallel) into `run/B33_ticketmetadata_shadow_fix_and_gpt5_models`
- [x] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/B33_ticketmetadata_shadow_fix_and_gpt5_models` â†’ `main` (PR with merge commit)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branch after merge
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
