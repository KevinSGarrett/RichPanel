# Documentation Policy

**Doc ID:** POL-DOCS-001  
**Source:** `Policies.zip` (extended/hardened in Wave F05)  
**Last verified:** 2025-12-29  

This policy defines how documentation must be maintained so AI agents can reliably navigate, update, and verify the system without drifting.

## Non-negotiables
1. **Documentation coverage gate**
   - If you change behavior, there must be documentation that explains the new behavior.
   - If no doc exists for an impacted area, create it in the correct folder and link it from `docs/INDEX.md`.

2. **Proof of what was reviewed vs changed**
   - For any run, report what you read and what you changed.
   - Prefer writing a short “Docs impact” summary using:
     - `docs/98_Agent_Ops/Templates/Docs_Run_Update_Checklist_TEMPLATE.md`

3. **Index-first navigation**
   - Always consult: `docs/INDEX.md`, `docs/CODEMAP.md`, and module READMEs before broad searching.
   - If you had to search widely, improve the index/codemap.

4. **Chunking and token efficiency**
   - Use clear H2 sections (chunkable).
   - Keep docs short; link out to deeper files instead of duplicating.

## Living Documentation Set (always update when relevant)
Canonical list: `docs/98_Agent_Ops/Living_Documentation_Set.md`

**At minimum, consider updates to:**
- `CHANGELOG.md`
- `docs/00_Project_Admin/Decision_Log.md`
- `docs/00_Project_Admin/Issue_Log.md` + `docs/00_Project_Admin/Issues/`
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/00_Project_Admin/To_Do/`
- `docs/02_System_Architecture/System_Overview.md`
- `docs/02_System_Architecture/System_Matrix.md`
- `docs/04_API_Contracts/API_Reference.md` + `openapi.yaml`
- `config/.env.example` + `docs/09_Deployment_Operations/Environment_Config.md`
- `docs/08_Testing_Quality/Test_Evidence_Log.md` + `qa/test_evidence/`
- `docs/07_User_Documentation/User_Manual.md`
- Security docs: `docs/06_Security_Privacy_Compliance/` (when relevant)

## If you add or move docs
- Update:
  - `docs/INDEX.md`
  - `docs/CODEMAP.md`
- Regenerate:
  - `python scripts/regen_doc_registry.py`
  - `python scripts/verify_plan_sync.py`

## “Last verified” header rule
Every doc that is created or meaningfully edited must include:
- `Last verified: YYYY-MM-DD — <reason>`

## Template usage
When in doubt, use templates:
- `docs/98_Agent_Ops/Templates/Docs_Run_Update_Checklist_TEMPLATE.md`
- `docs/98_Agent_Ops/Templates/Changelog_Entry_TEMPLATE.md`
