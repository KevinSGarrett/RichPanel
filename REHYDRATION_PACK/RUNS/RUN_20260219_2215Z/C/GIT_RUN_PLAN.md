# Git Run Plan

Use this file to coordinate Git/GitHub execution for this run.

**RUN_ID:** RUN_20260219_2215Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/RUN_20260219_2215Z-B95C`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required; after merge)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (used)
- Agent C works on: `run/RUN_20260219_2215Z-B95C`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - none (not participating)
- Locked paths (do not edit):
  - all

### Agent B
- Allowed paths:
  - none (not participating)
- Locked paths:
  - all

### Agent C
- Allowed paths:
  - `backend/src/richpanel_middleware/automation/delivery_estimate.py`
  - `backend/src/richpanel_middleware/automation/pipeline.py`
  - `backend/src/richpanel_middleware/automation/order_status_prompts.py`
  - `backend/tests/test_delivery_estimate_fallback.py`
  - `backend/tests/test_order_status_reply_personalization.py`
  - `backend/tests/test_tracking_link_generation.py`
  - `scripts/test_delivery_estimate.py`
  - `scripts/test_e2e_smoke_encoding.py`
  - `scripts/test_live_readonly_shadow_eval.py`
  - `scripts/test_pipeline_handlers.py`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/_generated/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260219_2215Z/C/*`
- Locked paths:
  - all others

---

## Integration checklist (Integrator)
- [ ] Rebase onto latest `main`
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Open PR and wait for required checks
- [ ] Merge `run/RUN_20260219_2215Z-B95C` → `main` (merge commit)
- [ ] Delete run branch after merge
