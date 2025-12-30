# Wave F02 Changelog — Docs Indexing + Navigation Hardening

Date: 2025-12-28  
Mode: foundation

## Summary
This wave hardened the repo’s **AI retrieval** and eliminated ambiguity/drift risks in the documentation layer.

## Key changes
- Added a **full master wave schedule** into `REHYDRATION_PACK/`:
  - `WAVE_SCHEDULE.md` (quick view)
  - `WAVE_SCHEDULE_FULL.md` (authoritative)
  Both are tracked in `REHYDRATION_PACK/MANIFEST.yaml`.

- Removed “foundation vs build” confusion in pack entrypoints:
  - `REHYDRATION_PACK/00_START_HERE.md` now has explicit read order + attach guidance.
  - `PM_REHYDRATION_PACK/00_START_HERE.md` now has explicit read order (no placeholders).

- Clarified canonical vs legacy plan paths:
  - Added `docs/00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md`
  - Linked it from `docs/INDEX.md`

- Upgraded machine registries:
  - Enhanced `scripts/regen_doc_registry.py` to generate:
    - `docs/_generated/doc_registry.json` (includes status + in_index flags)
    - `docs/_generated/doc_outline.json`
    - `docs/_generated/heading_index.json`
  - Regenerated `docs/REGISTRY.md` and `_generated` outputs.

- Added AI retrieval workflow doc:
  - `docs/98_Agent_Ops/AI_Worker_Retrieval_Workflow.md` (linked from `docs/INDEX.md`)

## Validation
- `python scripts/verify_plan_sync.py`
- `python scripts/verify_rehydration_pack.py`
- `python scripts/regen_doc_registry.py`

## Next wave
- **Wave F03 — Pack + registry automation hardening**
