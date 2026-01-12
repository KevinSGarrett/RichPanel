# Run Meta

- RUN_ID: `RUN_20260112_0054Z`
- Mode: build
- Objective: Wire worker planning flags into plan_actions with ON/OFF coverage; capture artifacts for agents.
- Stop conditions: CI green and artifacts written; no further edits planned.

## Notes
- Each agent writes to its folder: A/, B/, C/.
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode).
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`.
