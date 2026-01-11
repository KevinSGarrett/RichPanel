# Git Run Plan

**RUN_ID:** RUN_20260110_2200Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** `run/B32_llm_reply_rewrite_20260110`  
**Merge strategy:** merge commit  
**Branch cleanup:** yes after merge

## Main branch rule
- `main` protected; changes land via PR.

## Branch plan
- Agent A had no active scope for this run; primary work handled by Agent C.

## Agent scope/locks
- Allowed: none (no work assigned).
- Locked: all paths.

## Integration checklist
- Pull latest `main` (handled by active agent).
- Ensure CI green.
- Merge PR and delete branch when complete.
