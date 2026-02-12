# Git Run Plan

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** RUN_20260212_0204Z  
**Mode:** sequential (single-agent)  
**Integrator:** N/A (single-agent run)  
**Target branch:** 77/preorder-eta  
**Merge strategy:** merge commit (required)  
**Branch cleanup:** no (human-owned)  

---

## Main branch rule
- main is protected: changes land via PR (required status checks; merge commit).

## Branch plan
### Sequential (single-agent)
- Agent A uses: b77/preorder-eta

### Parallel (not used)
- Agent B: N/A
- Agent C: N/A

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - backend/src/richpanel_middleware/automation/
  - scripts/
  - docs/00_Project_Admin/
  - docs/_generated/
  - REHYDRATION_PACK/RUNS/RUN_20260212_0204Z/
- Locked paths (do not edit):
  - NONE

### Agent B
- Allowed paths:
  - NONE (not used)
- Locked paths:
  - ALL

### Agent C
- Allowed paths:
  - NONE (not used)
- Locked paths:
  - ALL

---

## Integration checklist (Integrator)
- [ ] N/A (single-agent run)
