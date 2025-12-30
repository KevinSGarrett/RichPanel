# Wave F08 Changelog

Date: 2025-12-29  
Mode: foundation

## Summary
Registry synchronization + schedule clarity improvements, driven by a `verify_plan_sync.py` failure (registry count mismatch).

## Changes
- Converted legacy governance docs under `docs/10_Governance_Continuous_Improvement/` into explicit redirect stubs.
- Added `docs/00_Project_Admin/Wave_Naming_and_Mapping.md` to clarify F/B/C naming and where **B00** fits.
- Updated `docs/00_Project_Admin/Progress_Wave_Schedule.md` to reference rehydration pack schedule files as authoritative.
- Regenerated:
  - `docs/REGISTRY.md`
  - `docs/_generated/doc_registry.json`
  - `docs/_generated/doc_registry.compact.json`
  - `docs/_generated/doc_outline.json`
  - `docs/_generated/heading_index.json`
- Improved error reporting in `scripts/verify_plan_sync.py` (lists missing/extra doc paths).

## Validation
- `python scripts/verify_rehydration_pack.py` → OK
- `python scripts/verify_doc_hygiene.py` → OK
- `python scripts/verify_plan_sync.py` → OK
- `python scripts/regen_doc_registry.py` → OK

