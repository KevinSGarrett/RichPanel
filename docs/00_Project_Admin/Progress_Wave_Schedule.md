# Progress & Wave Schedule

Last updated: 2025-12-29 — Wave F08

This document tracks **progress** and points to the **authoritative wave schedule**.

## Authoritative schedule (source of truth)

The master schedule lives in the rehydration pack:

- `REHYDRATION_PACK/WAVE_SCHEDULE.md` (quick)
- `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` (full; authoritative)

If any other file disagrees, treat the rehydration pack schedule as canonical.

## Wave naming (F / B / C)

This repo uses phase-prefixed waves:

- **Fxx** = Foundation (structure/docs/policies/indexes/automation). No Cursor runs required.
- **Bxx** = Build (implementation with Cursor agents and per-run artifacts).
- **Cxx** = Continuous improvement.

Details and mapping from the earlier “Wave 00–10” draft schedule:
- `Wave_Naming_and_Mapping.md`

## Current status summary

### Foundation (mode: `foundation`)
Completed foundation waves:
- F00–F07 complete
- **F08 complete** (registry sync + schedule clarity)

### Build (mode: `build`) — not started
Next build step:
- Complete `Build_Mode_Activation_Checklist.md`
- Switch `REHYDRATION_PACK/MODE.yaml` to `mode: build`
- Begin **B00** (build kickoff + CI baseline)

## Next actions

- Review: `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- When ready: say “continue to B00” and we will generate the first build-mode scaffolding updates.

