# Run Meta

- RUN_ID: `RUN_20260116_0236Z`
- Mode: build
- Objective: Adopt NewWorkflows Phase 1 artifacts for risk labels, label seeding, staleness, and optional Claude gate.
- Stop conditions: Local CI-equivalent pass; PR labeled with risk; Bugbot + Codecov green; run artifacts populated.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
