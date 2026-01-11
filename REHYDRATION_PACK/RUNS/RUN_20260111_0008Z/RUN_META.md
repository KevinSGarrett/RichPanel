# Run Meta

- RUN_ID: `RUN_20260111_0008Z`
- Mode: build
- Objective: Resolve TicketMetadata shadowing, align middleware to GPT-5.2 defaults, and ship with CI evidence + PR/auto-merge.
- Stop conditions: CI-equivalent green; run artifacts updated; PR opened with auto-merge enabled.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
