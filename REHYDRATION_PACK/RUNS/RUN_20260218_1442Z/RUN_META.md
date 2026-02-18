# Run Meta

- RUN_ID: `RUN_20260218_1442Z`
- Mode: build
- Objective: Add deterministic Key Details block to ETA/no-tracking replies and preserve through rewrite with tests.
- Stop conditions: Key Details present for eligible ETA replies, late/no-window excluded, tests updated, CI/pytest evidence recorded.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
