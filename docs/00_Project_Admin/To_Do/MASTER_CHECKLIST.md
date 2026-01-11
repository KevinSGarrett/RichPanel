# MASTER CHECKLIST (Epics / Milestones)

Last verified: 2026-01-11 — Codecov + model default alignment pass.

This checklist is the **high-level map** of work required to complete the project.
It stays intentionally short; atomic tasks live in `PLAN_CHECKLIST.md` (and generated outputs).

## Progress dashboard (repo-shipped vs roadmap)

Status definitions used here:
- **Shipped**: merged into the repo (code/docs/workflows exist)
- **In progress**: actively being implemented in the repo
- **Roadmap**: not shipped yet (planned/pending)

As of 2026-01-11 (based on the table below):
- Total epics: 20
- Shipped: 10 (50.0%)
- In progress: 2 (10.0%)
- Roadmap: 8 (40.0%)

Important:
- This file does **not** assert live environment state (dev/staging/prod). Only mark deployments/smoke tests as verified when there is explicit linked evidence (e.g., GitHub Actions run URLs, runbook evidence logs).

| ID | Epic | Status | Primary owner | References |
|---|---|---|---|---|
| CHK-001 | Foundation: Documentation OS complete | Shipped | PM | `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` |
| CHK-002 | Foundation: Plan → checklist extraction automated | Shipped | PM | `scripts/regen_plan_checklist.py`, `PLAN_CHECKLIST.md` |
| CHK-003 | Build readiness: Activate build mode | Shipped | PM | `REHYDRATION_PACK/MODE.yaml`, `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md` |
| CHK-004 | Foundation: CR-001 no-tracking ETA + controlled auto-close policy (spec + policy updates) | Shipped | PM | `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md` |
| CHK-005 | CI gates: CI-equivalent checks + admin anti-drift + run-report enforcement | Shipped | PM | `scripts/run_ci_checks.py`, `scripts/verify_rehydration_pack.py`, `scripts/verify_admin_logs_sync.py` |
| CHK-006 | Dev/Staging deploy workflows (GitHub Actions) | Shipped | Agent A | `.github/workflows/deploy-dev.yml`, `.github/workflows/deploy-staging.yml` |
| CHK-007 | Dev/Staging E2E smoke tests (GitHub Actions) | Shipped | Agent A | `.github/workflows/dev-e2e-smoke.yml`, `.github/workflows/staging-e2e-smoke.yml` |
| CHK-008 | Build: Offline-first integration skeletons (Richpanel/OpenAI/Shopify/ShipStation) | Shipped (skeleton) | Agent A | `backend/src/richpanel_middleware/integrations/`, `backend/src/integrations/` |
| CHK-009 | Process: Bugbot in PR loop (trigger + runbook) | Shipped | PM | `docs/08_Engineering/CI_and_Actions_Runbook.md` |
| CHK-010 | Build: Ingest + persist (idempotency + state + audit) + ACK-fast + enqueue | In progress | Agent A | `backend/src/lambda_handlers/ingress/handler.py`, `backend/src/lambda_handlers/worker/handler.py`, `scripts/dev_e2e_smoke.py`, `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| CHK-011 | Build: Router MVP (intent → dept) | Roadmap | Agent B | `docs/04_LLM_Design_Evaluation/` |
| CHK-012 | Build: Automation MVP (FAQ / order status) | Roadmap | Agent C | `docs/05_FAQ_Automation/` |
| CHK-013 | Build: Observability + audit trail | In progress | Agent C | `scripts/dev_e2e_smoke.py`, `docs/08_Observability_Analytics/` |
| CHK-014 | Build: Security controls + compliance readiness | Roadmap | Agent A | `docs/06_Security_Privacy_Compliance/` |
| CHK-015 | Build: Richpanel UI configuration (teams/tags/macros/automation triggers) | Roadmap | Ops + PM | `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md` |
| CHK-016 | Build: Production go-live (human go/no-go + prod promotion checklist + enablement) | Roadmap | PM + Ops | `docs/00_Project_Admin/Progress_Log.md`, `.github/workflows/deploy-prod.yml`, `.github/workflows/prod-e2e-smoke.yml` |
| CHK-017 | Build: Real outbound automation (email/SMS/notifications) | Roadmap | Agent C | `docs/07_Notifications_Outbound/` |
| CHK-018 | CI: Codecov upload wired in CI (advisory, non-blocking) | Shipped | Agent B | `.github/workflows/ci.yml`, `codecov.yml`, `docs/08_Engineering/CI_and_Actions_Runbook.md` |
| CHK-019 | CI: Codecov branch-protection required status checks enabled | Roadmap | PM + Eng | `codecov.yml`, `branch_protection_main.json` |
| CHK-020 | Build: Middleware OpenAI defaults moved to GPT-5.x family (no GPT-4/4o) | Roadmap | Agent B | `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`, `backend/src/richpanel_middleware/automation/prompts.py`, `backend/src/richpanel_middleware/automation/llm_routing.py` |

Notes:
- Build owners can be adjusted as build mode progresses.
- Keep this file small; detailed tasks belong in `PLAN_CHECKLIST.md` and source docs.
