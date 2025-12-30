# MASTER CHECKLIST (Epics / Milestones)

Last verified: 2025-12-29 — Wave F13.

This checklist is the **high-level map** of work required to complete the project.
It stays intentionally short; atomic tasks live in `PLAN_CHECKLIST.md` (and generated outputs).

| ID | Epic | Status | Primary owner | References |
|---|---|---|---|---|
| CHK-001 | Foundation: Documentation OS complete | ✅ Done | PM | `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` |
| CHK-002 | Foundation: Plan → checklist extraction automated | ✅ Done | PM | `scripts/regen_plan_checklist.py`, `PLAN_CHECKLIST.md` |
| CHK-003 | Build readiness: Activate build mode | ⏳ Pending | PM | `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md` |
| CHK-004 | Foundation: CR-001 no-tracking ETA + controlled auto-close policy | ⏳ Pending | PM | `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md` |
| CHK-010 | Build: Ingest + ACK-fast + enqueue | Not started | Agent A | `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| CHK-011 | Build: Router MVP (intent → dept) | Not started | Agent B | `docs/04_LLM_Design_Evaluation/` |
| CHK-012 | Build: Automation MVP (FAQ / order status) | Not started | Agent C | `docs/05_FAQ_Automation/` |
| CHK-013 | Build: Observability + audit trail | Not started | Agent C | `docs/08_Observability_Analytics/` |
| CHK-014 | Build: Security controls + compliance readiness | Not started | Agent A | `docs/06_Security_Privacy_Compliance/` |
| CHK-015 | Build: Deployment to staging/prod + runbooks | Not started | Agent A | `docs/09_Deployment_Operations/`, `docs/10_Operations_Runbooks_Training/` |

Notes:
- Build owners can be adjusted when we begin build mode.
- Keep this file small; detailed tasks belong in `PLAN_CHECKLIST.md` and source docs.
