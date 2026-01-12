# Run Meta

- RUN_ID: `RUN_20260111_2301Z`
- Mode: build
- Objective: Richpanel outbound smoke proof (Agent B active; A/C idle placeholders)
- Stop conditions: proof captured or AWS/test-ticket unavailable

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
