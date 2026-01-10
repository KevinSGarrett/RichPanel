# Next Actions (PM)

Last updated: 2025-12-29 — Wave F11

## Current status
- Foundation validators: passing
- Multi-agent GitHub guardrails: documented + scripted
- Rehydration pack: manifest-driven and validated

## Next logical step (if starting implementation)
1) Decide GitHub settings (PR required vs direct push to main)
2) Configure one-time agent auth (recommended: GitHub CLI `gh` + token)
3) Flip `REHYDRATION_PACK/MODE.yaml` to `mode: build`
4) Create first run folder:
   ```bash
   python scripts/new_run_folder.py --now
   ```
5) Populate:
   - `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md`
   - `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`

## If staying in foundation mode
- No further foundational gaps identified; proceed only if new requirements appear.

## Wave F13 next actions
- Confirm shipping method mapping + preorder ETA source + business-day calendar choice
- Confirm Richpanel resolve/reopen behavior
- Approve final message copy for `t_order_eta_no_tracking_verified`
