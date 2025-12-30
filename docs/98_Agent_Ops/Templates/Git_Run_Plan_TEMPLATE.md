# Git Run Plan (Template)

Use this file to coordinate Git/GitHub execution for a run.

**RUN_ID:** <RUN_ID>  
**Mode:** <sequential|parallel>  
**Integrator:** <A|B|C>  
**Target branch:** `run/<RUN_ID>`  
**Merge strategy:** <merge commit|squash>  
**Branch cleanup:** <yes/no>  

---

## Branch plan
### Sequential (default)
- All agents use: `run/<RUN_ID>`

### Parallel (only when scopes are disjoint)
- Agent A: `run/<RUN_ID>-A`
- Agent B: `run/<RUN_ID>-B`
- Agent C: `run/<RUN_ID>-C`
- Integrator merges into `run/<RUN_ID>`

---

## Agent scopes and locks (required)

### Agent A
- Allowed paths:
  - <path patterns>
- Locked paths (do not edit):
  - <path patterns>

### Agent B
- Allowed paths:
  - <path patterns>
- Locked paths:
  - <path patterns>

### Agent C
- Allowed paths:
  - <path patterns>
- Locked paths:
  - <path patterns>

---

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge agent branches (if parallel) into `run/<RUN_ID>`
- [ ] Run: `python scripts/run_ci_checks.py`
- [ ] Merge `run/<RUN_ID>` → `main` (PR preferred)
- [ ] Confirm Actions are green (or document failure + fix)
- [ ] Delete run branches + agent branches
- [ ] Update: `REHYDRATION_PACK/GITHUB_STATE.md`
