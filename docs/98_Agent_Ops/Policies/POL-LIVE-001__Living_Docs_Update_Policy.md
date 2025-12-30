# Living Docs Update Policy

**Doc ID:** POL-LIVE-001  
**Last verified:** 2025-12-29 — Wave F05.

This policy ensures the repository maintains a complete, continuously updated history of the build.

## The rule
If a change affects a “living” area of the system, you must update the corresponding living doc(s).

Canonical list: `docs/98_Agent_Ops/Living_Documentation_Set.md`

## Minimum required updates by change type

### API / endpoints changed
- Update: `docs/04_API_Contracts/openapi.yaml`
- Update: `docs/04_API_Contracts/API_Reference.md`
- Update: `docs/02_System_Architecture/System_Matrix.md`
- Add evidence: `docs/08_Testing_Quality/Test_Evidence_Log.md`
- Update: `CHANGELOG.md`

### Env/config changed
- Update: `config/.env.example`
- Update: `docs/09_Deployment_Operations/Environment_Config.md`
- Update: `docs/02_System_Architecture/System_Matrix.md`
- Update: `CHANGELOG.md`

### Bug fix
- Create issue file: `docs/00_Project_Admin/Issues/<ISSUE-ID>__*.md`
- Update: `docs/00_Project_Admin/Issue_Log.md`
- Add evidence: `docs/08_Testing_Quality/Test_Evidence_Log.md`
- Update: `CHANGELOG.md`

### Architecture/scope decision
- Update: `docs/00_Project_Admin/Decision_Log.md`
- Update: `CHANGELOG.md` (if meaningful)
- Update system docs if the decision changes architecture/config/API

## Use the checklist template
For each run, fill:
- `docs/98_Agent_Ops/Templates/Docs_Run_Update_Checklist_TEMPLATE.md`
