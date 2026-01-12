# Git Run Plan

**RUN_ID:** RUN_20260112_0054Z  
**Mode:** sequential  
**Integrator:** C  
**Target branch:** run/RUN_20260112_0054Z_worker_flag_wiring_only  
**Merge strategy:** merge commit  
**Branch cleanup:** yes

## Main branch rule
- `main` is protected; changes land via PR with required status checks.

## Branch plan
- Single branch: run/RUN_20260112_0054Z_worker_flag_wiring_only (worker wiring scope).

## Agent scopes and locks
- Agent A/B: idle for this run.
- Agent C: worker wiring, tests, CI helper, run artifacts for RUN_20260112_0054Z, and generated registries.

## Integration checklist (Integrator)
- [ ] Pull latest `main`
- [ ] Merge run/RUN_20260112_0054Z_worker_flag_wiring_only into `main`
- [ ] Run: `python scripts/run_ci_checks.py --ci`
- [ ] Confirm Actions are green
- [ ] Delete run branches if policy allows
- [ ] Update run records as needed
