# Docs Run Update Checklist

**Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`  
**Agent:** A | B | C  
**Date:** YYYY-MM-DD

Use this checklist to ensure the repo remains navigable and low‑drift.

## If you changed any docs
- [ ] Update `docs/INDEX.md` if navigation changed
- [ ] Update `docs/CODEMAP.md` if structure changed
- [ ] Run `python scripts/regen_doc_registry.py`
- [ ] Run `python scripts/verify_plan_sync.py`

## If you changed reference/vendor docs
- [ ] Run `python scripts/regen_reference_registry.py`

## If you changed plan checklist source docs
- [ ] Run `python scripts/regen_plan_checklist.py`

## Always-update living docs (when relevant)
- [ ] `CHANGELOG.md`
- [ ] `docs/00_Project_Admin/Decision_Log.md`
- [ ] `docs/00_Project_Admin/Issue_Log.md`
- [ ] `docs/02_System_Architecture/System_Matrix.md`
- [ ] `docs/04_API_Contracts/openapi.yaml`
- [ ] `config/.env.example`
