# Git Run Plan

**RUN_ID:** RUN_20260111_0512Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/B32_llm_reply_rewrite_20260110`  
**Merge strategy:** merge commit  
**Branch cleanup:** yes after merge

---

## Main branch rule
- `main` protected; PR required.

## Branch plan
- Agent B not active; primary work handled by Agent C.

## Agent scopes and locks (required)
- Agent B allowed: none (no tasks)
- Agent B locked: all paths

## Integration checklist (Integrator)
- Pull latest `main`
- Ensure CI green (`python scripts/run_ci_checks.py`)
- Merge PR #72 and delete branch when done
