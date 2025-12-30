# Wave F05 Changelog — Policy + template hardening

Date: 2025-12-29

## Summary
This wave focused on making the repository **self-documenting** for AI workers by:
- establishing a mandatory **Living Documentation Set**
- hardening policies and templates so continuous updates are enforced
- creating missing foundational living docs (API refs, env config, issue/progress logs, test evidence log, user manual, system matrix)

## Added (new)
- `CHANGELOG.md` (repo-level canonical changelog)
- Living docs:
  - `docs/02_System_Architecture/System_Overview.md`
  - `docs/02_System_Architecture/System_Matrix.md`
  - `docs/04_API_Contracts/` (`API_Reference.md`, `openapi.yaml`, `README.md`)
  - `docs/09_Deployment_Operations/Environment_Config.md`
  - `config/README.md`
  - `config/.env.example`
  - `docs/00_Project_Admin/Issue_Log.md`
  - `docs/00_Project_Admin/Issues/ISSUE_TEMPLATE.md`
  - `docs/00_Project_Admin/Progress_Log.md`
  - `docs/00_Project_Admin/To_Do/*` (checklist system)
  - `docs/08_Testing_Quality/Test_Evidence_Log.md`
  - `qa/test_evidence/README.md`
  - `docs/07_User_Documentation/*` (user manual scaffold)
  - `docs/98_Agent_Ops/Living_Documentation_Set.md`
- Policies:
  - `docs/98_Agent_Ops/Policies/POL-LIVE-001__Living_Docs_Update_Policy.md`
- Templates:
  - changelog entry, decision record, test evidence entry, docs update checklist, config/env change
  - stored in `docs/98_Agent_Ops/Templates/` and mirrored in `REHYDRATION_PACK/_TEMPLATES/`
- Pack pointers:
  - `REHYDRATION_PACK/CORE_LIVING_DOCS.md`
  - `REHYDRATION_PACK/ISSUES_SINCE_LAST.md`
  - `REHYDRATION_PACK/TESTS_SINCE_LAST.md`

## Updated
- `docs/INDEX.md` (added “Core living docs” section)
- `docs/CODEMAP.md` (added config/API/test-evidence placement)
- `docs/98_Agent_Ops/Policies/`:
  - `POL-DOCS-001`, `POL-TEST-001`, `POL-STRUCT-001` hardened/extended
- `REHYDRATION_PACK/`:
  - `MANIFEST.yaml` fixed (valid YAML) + updated for new files
  - `00_START_HERE.md` rewritten (no placeholders)
  - schedule + task board updated to reflect Wave F05 done
- `scripts/verify_plan_sync.py`:
  - now enforces presence of the Living Documentation Set

## Validation
All of the following should pass after applying this wave:
```bash
python scripts/verify_rehydration_pack.py
python scripts/regen_doc_registry.py
python scripts/regen_reference_registry.py
python scripts/verify_plan_sync.py
```
