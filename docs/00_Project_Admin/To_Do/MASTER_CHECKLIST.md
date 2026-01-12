# MASTER CHECKLIST (Epics / Milestones)

Last verified: 2026-01-10 - RUN_20260110_1445Z

This checklist is the **high-level map** of work required to complete the project.
It stays intentionally short; atomic tasks live in `PLAN_CHECKLIST.md` (and generated outputs).

## Progress dashboard (snapshot)

- Total epics: 21
- Done: 10 (47.6%)
- In progress: 2 (9.5%)
- Not started: 6 (28.6%)
- Pending: 3 (14.3%)

> Note: "Done" can include "Done (skeleton)" where only scaffolding exists.

## Shipped (completed)

| ID | Epic | Status | Primary owner | References |
|---|---|---|---|---|
| CHK-001 | Foundation: Documentation OS complete | Done | PM | `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` |
| CHK-002 | Foundation: Plan -> checklist extraction automated | Done | PM | `scripts/regen_plan_checklist.py`, `PLAN_CHECKLIST.md` |
| CHK-003 | Build readiness: Activate build mode | Done | PM | `REHYDRATION_PACK/MODE.yaml`, `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md` |
| CHK-004 | Foundation: CR-001 no-tracking ETA + controlled auto-close policy (spec + policy updates) | Done | PM | `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md` |
| CHK-005 | CI gates: CI-equivalent checks + admin anti-drift enforcement | Done | PM | `scripts/run_ci_checks.py`, `scripts/verify_admin_logs_sync.py` |
| CHK-006 | Dev/Staging deploy workflows (GitHub Actions) | Done | Agent A | `.github/workflows/deploy-dev.yml`, `.github/workflows/deploy-staging.yml` |
| CHK-007 | Dev/Staging E2E smoke tests (GitHub Actions) | Done | Agent A | `.github/workflows/dev-e2e-smoke.yml`, `.github/workflows/staging-e2e-smoke.yml` |
| CHK-008 | Build: Offline-first integration skeletons (Richpanel/OpenAI/Shopify/ShipStation) | Done (skeleton) | Agent A | `backend/src/richpanel_middleware/integrations/`, `backend/src/integrations/` |
| CHK-009 | Process: Bugbot in PR loop (trigger + runbook) | Done | PM | `docs/08_Engineering/CI_and_Actions_Runbook.md` |
| CHK-009B | Process: PR Health Check gates (Bugbot + Codecov + E2E) enforced in templates/runbooks | Done | Agent A | `REHYDRATION_PACK/_TEMPLATES/`, `docs/08_Engineering/CI_and_Actions_Runbook.md` |

## Roadmap (remaining)

| ID | Epic | Status | Primary owner | References |
|---|---|---|---|---|
| CHK-010 | Build: Ingest + persist (idempotency + state + audit) + ACK-fast + enqueue | In progress | Agent A | `backend/src/lambda_handlers/ingress/handler.py`, `backend/src/lambda_handlers/worker/handler.py`, `scripts/dev_e2e_smoke.py`, `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| CHK-010A | LLM: Per-workload OpenAI model env vars + defaults GPT‑5.x | Not started | Agent A | `docs/08_Engineering/OpenAI_Model_Plan.md`, `backend/src/richpanel_middleware/automation/llm_routing.py`, `backend/src/integrations/openai/client.py` |
| CHK-010B | LLM: Responses API + Structured Outputs migration (routing first, then verifier) | Not started | Agent A | `docs/08_Engineering/OpenAI_Model_Plan.md`, `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md` |
| CHK-011 | Build: Router MVP (intent -> dept) | Not started | Agent B | `docs/04_LLM_Design_Evaluation/` |
| CHK-012 | Build: Automation MVP (FAQ / order status) | Not started | Agent C | `docs/05_FAQ_Automation/` |
| CHK-013 | Build: Observability + audit trail | In progress | Agent C | `scripts/dev_e2e_smoke.py`, `docs/08_Observability_Analytics/` |
| CHK-014 | Build: Security controls + compliance readiness | Not started | Agent A | `docs/06_Security_Privacy_Compliance/` |
| CHK-015 | Build: Richpanel UI configuration (teams/tags/macros/automation triggers) | Pending | Ops + PM | `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md` |
| CHK-016 | Build: Production go-live (human go/no-go + prod promotion checklist + enablement) | Pending | PM + Ops | `docs/00_Project_Admin/Progress_Log.md`, `.github/workflows/deploy-prod.yml`, `.github/workflows/prod-e2e-smoke.yml` |
| CHK-017 | Build: Real outbound automation (email/SMS/notifications) | Pending | Agent C | `docs/07_Notifications_Outbound/` |
| CHK-018 | Midpoint audit: WaveAudit checklist + evidence gates | Not started | PM | `docs/00_Project_Admin/To_Do/MIDPOINT_AUDIT_CHECKLIST.md` |

Notes:
- Build owners can be adjusted as build mode progresses.
- Keep this file small; detailed tasks belong in `PLAN_CHECKLIST.md` and source docs.
- Do not claim dev/staging/prod state here unless linked to verified evidence.
