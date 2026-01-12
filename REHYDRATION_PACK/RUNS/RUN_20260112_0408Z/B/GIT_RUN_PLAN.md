# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260112_0408Z  
**Mode:** single agent  
**Integrator:** B (Engineering)  
**Target branch:** `run/RUN_20260112_0408Z_e2e_proof_pii_sanitize`  
**Merge strategy:** merge commit (locked)  
**Branch cleanup:** yes (required)  

---

## Main branch rule
- `main` is protected: changes land via PR (required status checks; merge commit).

## Branch plan
Single agent execution:
- Branch: `run/RUN_20260112_0408Z_e2e_proof_pii_sanitize`

---

## Agent scopes and locks

### Agent B (Engineering)
- Allowed paths:
  - `scripts/dev_e2e_smoke.py`
  - `docs/08_Engineering/CI_and_Actions_Runbook.md`
  - `REHYDRATION_PACK/RUNS/RUN_20260112_0259Z/B/*`
  - `REHYDRATION_PACK/RUNS/RUN_20260112_0408Z/B/*`
- Locked paths:
  - None (single agent run)

---

## Integration checklist (completed)
- [x] Pull latest `main`
- [x] Run: `python scripts/run_ci_checks.py --ci`
- [x] Create PR #83
- [x] Confirm CI green
- [x] PR #83 merged (auto-merge)
- [x] PR #84 (cleanup) merged
- [x] Branches auto-deleted
