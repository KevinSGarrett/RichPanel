# Wave F06 — Changelog

Date: 2025-12-29

## Summary
Wave F06 focuses on “foundation readiness”: making sure the documentation OS is complete, navigable, and enforceable before switching to build mode.

## Changes

### Foundation readiness + build-mode activation
- Added `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- Added `REHYDRATION_PACK/FOUNDATION_STATUS.md` (token-efficient readiness snapshot)
- Updated `REHYDRATION_PACK/MODE.yaml` to reflect current wave

### Plan → checklist extraction
- Added `scripts/regen_plan_checklist.py`
- Added generated plan checklist outputs:
  - `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`
  - `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`
- Rewrote `docs/00_Project_Admin/To_Do/PLAN_CHECKLIST.md` to explain the generated workflow

### Canonical vs legacy cleanup
- Standardized legacy redirect folders with MOVED stubs:
  - `docs/06_Data_Privacy_Observability/`
  - `docs/10_Governance_Continuous_Improvement/`
  - `docs/11_Cursor_Agent_Work_Packages/`
- Added `docs/00_Project_Admin/Legacy_Folder_Redirects.md`
- Rewrote `docs/00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md`

### Navigation + hygiene
- Updated `docs/INDEX.md` (living docs links)
- Rewrote `docs/CODEMAP.md` and `docs/ROADMAP.md`
- Added placeholder/draft standard doc:
  - `docs/98_Agent_Ops/Placeholder_and_Draft_Standards.md`

### Validation updates
- Updated `scripts/README.md`
- Updated `scripts/verify_plan_sync.py` to validate plan checklist outputs (generated)

## Evidence
Run:
- `python scripts/verify_rehydration_pack.py`
- `python scripts/regen_doc_registry.py`
- `python scripts/regen_reference_registry.py`
- `python scripts/regen_plan_checklist.py`
- `python scripts/verify_plan_sync.py`

