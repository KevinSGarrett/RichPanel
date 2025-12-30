# Wave F04 Changelog — Reference Indexing + Documentation Normalization

Date: 2025-12-29

## What shipped

### 1) Richpanel vendor/reference indexing (human + machine)
- Added curated vendor navigation:
  - `reference/richpanel/INDEX.md` (topic buckets + recommended entry docs)
  - `reference/richpanel/TOP_20.md` (fast entry to most-used vendor docs)
- Added machine registries:
  - `reference/_generated/reference_registry.json`
  - `reference/richpanel/_generated/reference_registry.json`
- Added generator:
  - `scripts/regen_reference_registry.py`
- Updated `reference/INDEX.md` to point to the curated navigation + registries.

### 2) Plan ↔ vendor cross-linking
- Added canonical crosswalk:
  - `docs/03_Richpanel_Integration/Vendor_Doc_Crosswalk.md`
- Updated `docs/INDEX.md` to link to the crosswalk + vendor reference index.

### 3) Retrieval workflow + citation guidance (anti-drift)
- Rewrote and hardened:
  - `docs/98_Agent_Ops/AI_Worker_Retrieval_Workflow.md`
  - includes: canonical vs reference flow, machine registry usage, and citation formats

### 4) Canonical vs legacy path clarity
- Rewrote:
  - `docs/00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md`
- Added/updated legacy folder markers:
  - `docs/10_Governance_Continuous_Improvement/MOVED.md`
  - `docs/11_Cursor_Agent_Work_Packages/MOVED.md`
  - `docs/06_Data_Privacy_Observability/README.md`
  - `docs/Waves/README.md`

### 5) Stable chunk headings for indexed docs
- Added structured H2 sections where missing:
  - `docs/00_Project_Admin/Risk_Register.md`
  - `docs/09_Deployment_Operations/Runbooks.md`
  - `docs/12_Cursor_Agent_Work_Packages/01_Work_Breakdown/Dependency_Map.md`
- Added audit:
  - `docs/00_Project_Admin/Doc_Chunking_Audit.md`

### 6) Script + validation updates
- Updated:
  - `scripts/README.md` (foundation workflow includes reference registry)
  - `scripts/verify_plan_sync.py` (now validates reference registry + fixed link parsing)

### 7) Rehydration pack updates
- Updated `REHYDRATION_PACK/` to reflect Wave F04 completion and Wave F05 next:
  - `00_START_HERE.md`
  - `02_CURRENT_STATE.md`
  - `03_ACTIVE_WORKSTREAMS.md`
  - `05_TASK_BOARD.md`
  - `WAVE_SCHEDULE.md`
  - `WAVE_SCHEDULE_FULL.md`
  - `LAST_REHYDRATED.md`

## Validation
- `python scripts/verify_rehydration_pack.py` ✅
- `python scripts/regen_doc_registry.py` ✅
- `python scripts/regen_reference_registry.py` ✅
- `python scripts/verify_plan_sync.py` ✅

## Next wave
- **Wave F05 — Policy + template hardening**
  - See `REHYDRATION_PACK/05_TASK_BOARD.md`
