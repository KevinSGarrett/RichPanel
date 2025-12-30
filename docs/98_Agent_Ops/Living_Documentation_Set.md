# Living Documentation Set (Always-Update Docs)

Last verified: 2025-12-29 — Wave F06 (living docs list finalized + linked from INDEX).

These documents are intended to be **continuously updated** throughout the build so an AI agent can:

- reconstruct what was built
- understand why decisions were made
- locate configuration and API surfaces
- see test evidence and issue history
- operate the system safely (security/privacy) and reliably (SLOs/runbooks)

This file defines the **canonical list** and **update triggers**.

---

## Canonical living docs (paths)

### System understanding
- **System overview:** `docs/02_System_Architecture/System_Overview.md`
- **System matrix (components map):** `docs/02_System_Architecture/System_Matrix.md`

### Interfaces / contracts
- **API reference (human):** `docs/04_API_Contracts/API_Reference.md`
- **OpenAPI source of truth (machine):** `docs/04_API_Contracts/openapi.yaml`

### Configuration
- **Env template (non-secret):** `config/.env.example`
- **Environment configuration guide:** `docs/09_Deployment_Operations/Environment_Config.md`

### Decisions & progress
- **Decision log:** `docs/00_Project_Admin/Decision_Log.md`
- **Progress log:** `docs/00_Project_Admin/Progress_Log.md`
- **Current snapshot (token-efficient):** `REHYDRATION_PACK/02_CURRENT_STATE.md`

### Issues & fixes
- **Issue index:** `docs/00_Project_Admin/Issue_Log.md`
- **Issue details:** `docs/00_Project_Admin/Issues/` (one file per issue)

### Testing & evidence
- **Test evidence log:** `docs/08_Testing_Quality/Test_Evidence_Log.md`
- **Raw evidence artifacts:** `qa/test_evidence/`

### User / operator documentation
- **User manual:** `docs/07_User_Documentation/User_Manual.md`
- **Operations handbook:** `docs/10_Operations_Runbooks_Training/Operations_Handbook.md`
- **Runbooks (index):** `docs/10_Operations_Runbooks_Training/Runbook_Index.md`

### Security & privacy
- **Security & privacy index:** `docs/06_Security_Privacy_Compliance/README.md`
- **PII handling + redaction:** `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`

### Repo-level history
- **Repository changelog (canonical):** `CHANGELOG.md`

### Work tracking
- **To-do system:** `docs/00_Project_Admin/To_Do/`
  - MASTER_CHECKLIST: `docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md`
  - PLAN_CHECKLIST (traceable): `docs/00_Project_Admin/To_Do/PLAN_CHECKLIST.md`
  - BACKLOG: `docs/00_Project_Admin/To_Do/BACKLOG.md`
  - DONE_LOG: `docs/00_Project_Admin/To_Do/DONE_LOG.md`

---

## Update triggers (rules of thumb)

### If you change code behavior
Update:
- API reference + OpenAPI
- system matrix
- test evidence log (+ attach raw evidence)
- changelog

### If you add/remove/rename env vars
Update:
- `config/.env.example`
- Environment config doc
- system matrix
- changelog

### If you fix a bug or a regression
Update:
- create an issue file under `docs/00_Project_Admin/Issues/`
- add a row to `Issue_Log.md`
- add test evidence (what failed before / what passed after)
- update changelog

### If you make an architectural/product decision
Update:
- decision log
- system overview / matrix if the decision changes architecture
- changelog (if it affects work direction)

---

## Token-efficient pointer map

The rehydration pack includes a pointer map for fast PM reads:
- `REHYDRATION_PACK/CORE_LIVING_DOCS.md`

