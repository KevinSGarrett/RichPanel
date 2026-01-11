# Git Run Plan

**RUN_ID:** RUN_20260111_0532Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/B32_llm_reply_rewrite_20260110`  
**Merge strategy:** merge commit  
**Branch cleanup:** yes after merge

## Main branch rule
- `main` protected; PR required.

## Branch plan
- Agent A inactive; primary work handled by Agent C.

## Agent scopes and locks
- Allowed: none (no tasks)
- Locked: all paths

## Integration checklist
- Ensure CI green (handled by Agent C).
- Merge PR and delete branch post-merge.
