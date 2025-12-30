# Wave F03 Changelog — Pack + Registry Automation Hardening

Date: 2025-12-29  
Mode: foundation

## Highlights
- Upgraded rehydration pack manifest to **MANIFEST v2** (mode-aware requirements).
- Hardened validation scripts:
  - `scripts/verify_rehydration_pack.py` (mode-aware strictness)
  - `scripts/verify_plan_sync.py` (docs + generated indexes validation)
- Updated rehydration pack entrypoint + guardrails (no placeholders, mode clarity).
- Expanded and clarified `docs/98_Agent_Ops/Rehydration_Pack_Spec.md`.
- Added `docs/98_Agent_Ops/Validation_and_Automation.md` and linked it from `docs/INDEX.md`.
- Regenerated docs registries under `docs/_generated/`.

## Validation status
- `python scripts/verify_rehydration_pack.py` ✅
- `python scripts/verify_plan_sync.py` ✅
- `python scripts/regen_doc_registry.py` ✅
