# MASTER CHECKLIST (Epics / Milestones)

Last verified: 2026-01-06 — run/B21_checklist_alignment_20260106.

This checklist is the **high-level map** of work required to complete the project.
It stays intentionally short; atomic tasks live in `PLAN_CHECKLIST.md` (and generated outputs).

| ID | Epic | Status | Primary owner | References |
|---|---|---|---|---|
| CHK-001 | Foundation: Documentation OS complete | ✅ Done | PM | `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` |
| CHK-002 | Foundation: Plan → checklist extraction automated | ✅ Done | PM | `scripts/regen_plan_checklist.py`, `PLAN_CHECKLIST.md` |
| CHK-003 | Build readiness: Activate build mode | ✅ Done | PM | `REHYDRATION_PACK/MODE.yaml`, `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md` |
| CHK-004 | Foundation: CR-001 no-tracking ETA + controlled auto-close policy (spec + policy updates) | ✅ Done | PM | `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md` |
| CHK-005 | CI gates: CI-equivalent checks + admin anti-drift enforcement | ✅ Done | PM | `scripts/run_ci_checks.py`, `scripts/verify_admin_logs_sync.py` |
| CHK-006 | Dev/Staging deploy workflows (GitHub Actions) | ✅ Done | Agent A | `.github/workflows/deploy-dev.yml`, `.github/workflows/deploy-staging.yml` |
| CHK-007 | Dev/Staging E2E smoke tests (GitHub Actions) | ✅ Done | Agent A | `.github/workflows/dev-e2e-smoke.yml`, `.github/workflows/staging-e2e-smoke.yml` |
| CHK-008 | Build: Offline-first integration skeletons (Richpanel/OpenAI/Shopify/ShipStation) | ✅ Done (skeleton) | Agent A | `backend/src/richpanel_middleware/integrations/`, `backend/src/integrations/` |
| CHK-009 | Process: Bugbot in PR loop (trigger + runbook) | ✅ Done | PM | `docs/08_Engineering/CI_and_Actions_Runbook.md` |
| CHK-010 | Build: Ingest + persist (idempotency + state + audit) + ACK-fast + enqueue | 🚧 In progress | Agent A | `backend/src/lambda_handlers/ingress/handler.py`, `backend/src/lambda_handlers/worker/handler.py`, `scripts/dev_e2e_smoke.py`, `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| CHK-011 | Build: Router MVP (intent → dept) | 🚧 In progress (dev/staging; prod pending) | Agent B | `backend/src/richpanel_middleware/automation/router.py`, `docs/04_LLM_Design_Evaluation/` |
| CHK-012 | Build: Automation MVP (FAQ / order status) | 🚧 In progress (dev/staging; prod pending) | Agent C | `backend/src/richpanel_middleware/automation/pipeline.py`, `backend/src/richpanel_middleware/automation/delivery_estimate.py`, `docs/05_FAQ_Automation/` |
| CHK-013 | Build: Observability + audit trail | 🚧 In progress (dev/staging; prod pending) | Agent C | `backend/src/lambda_handlers/worker/handler.py`, `scripts/dev_e2e_smoke.py`, `docs/08_Observability_Analytics/` |
| CHK-014 | Build: Security controls + compliance readiness | 🚧 In progress (kill switches + auth implemented; compliance docs pending) | Agent A | `backend/src/lambda_handlers/worker/handler.py`, `backend/src/lambda_handlers/ingress/handler.py`, `docs/06_Security_Privacy_Compliance/` |
| CHK-015 | Build: Richpanel UI configuration (teams/tags/macros/automation triggers) | ⏳ Pending | Ops + PM | `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md` |
| CHK-016 | Build: Production go-live (human go/no-go + prod promotion checklist + enablement) | ⏳ Pending | PM + Ops | `docs/00_Project_Admin/Progress_Log.md`, `.github/workflows/deploy-prod.yml`, `.github/workflows/prod-e2e-smoke.yml` |
| CHK-017 | Build: Real outbound automation (email/SMS/notifications) | ⏳ Pending | Agent C | `docs/07_Notifications_Outbound/` |

Notes:
- Build owners can be adjusted as build mode progresses.
- Keep this file small; detailed tasks belong in `PLAN_CHECKLIST.md` and source docs.
