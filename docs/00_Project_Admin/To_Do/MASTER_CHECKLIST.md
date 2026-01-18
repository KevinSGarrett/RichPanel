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
| CHK-010A | LLM: Per-workload OpenAI model env vars + defaults GPT-5.x | Not started | Agent A | `docs/08_Engineering/OpenAI_Model_Plan.md`, `backend/src/richpanel_middleware/automation/llm_routing.py`, `backend/src/integrations/openai/client.py`, `scripts/verify_openai_model_defaults.py` |
| CHK-010B | LLM: Responses API + Structured Outputs migration (routing first, then verifier) | Not started | Agent A | `docs/08_Engineering/OpenAI_Model_Plan.md`, `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md` |
| CHK-011 | Build: Router MVP (intent -> dept) | Not started | Agent B | `docs/04_LLM_Design_Evaluation/` |
| CHK-012 | Build: Automation MVP (FAQ / order status) | Not started | Agent C | `docs/05_FAQ_Automation/` |
| CHK-012A | Order Status Deployment Readiness | In progress | Agent B + C | See "Order Status Deployment Readiness" section below |
| CHK-013 | Build: Observability + audit trail | In progress | Agent C | `scripts/dev_e2e_smoke.py`, `docs/08_Observability_Analytics/` |
| CHK-014 | Build: Security controls + compliance readiness | Not started | Agent A | `docs/06_Security_Privacy_Compliance/` |
| CHK-015 | Build: Richpanel UI configuration (teams/tags/macros/automation triggers) | Pending | Ops + PM | `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md` |
| CHK-016 | Build: Production go-live (human go/no-go + prod promotion checklist + enablement) | Pending | PM + Ops | `docs/00_Project_Admin/Progress_Log.md`, `.github/workflows/deploy-prod.yml`, `.github/workflows/prod-e2e-smoke.yml` |
| CHK-017 | Build: Real outbound automation (email/SMS/notifications) | Pending | Agent C | `docs/07_Notifications_Outbound/` |
| CHK-018 | Midpoint audit: WaveAudit checklist + evidence gates | Not started | PM | `docs/00_Project_Admin/To_Do/MIDPOINT_AUDIT_CHECKLIST.md` |

---

## Order Status Deployment Readiness (CHK-012A)

**Goal:** Make Order Status automation operationally shippable with unambiguous E2E proof, read-only shadow mode validation, and production deployment gates.

**Status:** In progress (Agent B + C)

### E2E Proof Requirements

- [ ] **PASS_STRONG E2E proof exists for order_status_tracking scenario**
  - Webhook accepted (HTTP 200/202)
  - Idempotency + conversation_state + audit records observed in DynamoDB
  - Routing intent is `order_status_tracking`
  - Ticket status changed to `resolved` or `closed`
  - Reply evidence observed (message_count delta > 0 OR last_message_source=middleware)
  - Middleware tags applied: `mw-auto-replied`, `mw-order-status-answered`
  - No skip/escalation tags added this run
  - Proof JSON is PII-safe (ticket IDs hashed, paths redacted)
  - **Reference:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (Order Status Proof section)

- [ ] **PASS_STRONG E2E proof exists for order_status_no_tracking scenario**
  - All criteria from order_status_tracking above
  - Routing intent is `order_status_no_tracking`
  - ETA-based reply sent (no tracking URL/number)
  - Ticket auto-closed if within SLA window
  - **Reference:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (Order Status Proof section)

- [ ] **Follow-up behavior verified (loop prevention)**
  - Follow-up webhook sent after initial auto-reply
  - Worker routes follow-up to Email Support Team (no duplicate auto-reply)
  - Tags applied: `route-email-support-team`, `mw-escalated-human`, `mw-skip-followup-after-auto-reply`
  - Proof JSON records `routed_to_support=true` and no reply evidence
  - **Reference:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (Follow-up behavior verification)

### Read-Only Production Shadow Mode

- [ ] **Read-only production shadow mode verified (zero writes)**
  - Shadow mode control configured:
    - SSM parameters: `safe_mode=true`, `automation_enabled=false` (via set-runtime-flags.yml workflow)
    - Lambda env vars: `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`
    - Optional: `SHOPIFY_WRITE_DISABLED=true`
    - DEV override (if needed): `MW_ALLOW_ENV_FLAG_OVERRIDE=true`, `MW_AUTOMATION_ENABLED_OVERRIDE=false`, `MW_SAFE_MODE_OVERRIDE=true`
  - CloudWatch Logs audit confirms zero POST/PUT/PATCH/DELETE calls to Richpanel/Shopify
  - Middleware hard-fails on write attempts (raises `RichpanelWriteDisabledError`)
  - Test write operation confirmed to fail (no tags/comments/status changes in Richpanel)
  - Evidence stored in `qa/test_evidence/shadow_mode_validation/<RUN_ID>/`
  - **Reference:** `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`

### Observability and Monitoring

- [ ] **Alarms/metrics/logging verified**
  - CloudWatch dashboard exists: `rp-mw-<env>-ops`
  - Alarms configured:
    - `rp-mw-<env>-dlq-depth` (DLQ depth threshold)
    - `rp-mw-<env>-worker-errors` (Lambda error rate)
    - `rp-mw-<env>-worker-throttles` (Lambda throttle rate)
    - `rp-mw-<env>-ingress-errors` (API Gateway 5xx rate)
  - Logs include routing decisions, order lookup results, reply sent confirmations
  - PII redaction verified in CloudWatch Logs (no raw emails/phone/addresses)
  - **Reference:** `docs/08_Observability_Analytics/Logging_Metrics_Tracing.md`

### Code Quality and CI Gates

- [ ] **CI-equivalent checks pass**
  - `python scripts/run_ci_checks.py --ci` exits 0
  - Codecov patch coverage ≥50% (target ≥60%)
  - Bugbot review green (or manual review documented if quota exhausted)
  - No linter errors (ruff, black, mypy) in order status paths
  - **Reference:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (PR Health Check)

- [ ] **Unit/integration tests cover order status paths**
  - Order lookup (tracking/no-tracking scenarios)
  - ETA calculation (shipping bucket logic)
  - Template rendering (order variables, redaction)
  - Loop prevention (follow-up detection)
  - Write-disabled enforcement (RichpanelWriteDisabledError)
  - **Reference:** `docs/08_Testing_Quality/Integration_Test_Plan.md`

### Documentation and Runbooks

- [ ] **Order status automation spec is current**
  - Safety constraints documented (deterministic match, fail-closed)
  - Response selection matrix (tracking vs no-tracking vs ask-order-number)
  - De-duplication/loop prevention rules
  - **Reference:** `docs/05_FAQ_Automation/Order_Status_Automation.md`

- [ ] **Operator runbooks exist**
  - Production read-only shadow mode runbook
  - E2E smoke test runbook (tracking + no-tracking scenarios)
  - Incident response plan (how to disable flags, rollback)
  - **Reference:** `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`, `docs/08_Engineering/CI_and_Actions_Runbook.md`

### Deployment Gates

- [ ] **Staging deployment verified**
  - Deploy staging stack succeeded
  - Staging E2E smoke test passed (order_status_tracking + order_status_no_tracking)
  - Evidence captured in `REHYDRATION_PACK/RUNS/<RUN_ID>/A/TEST_MATRIX.md`
  - **Reference:** `.github/workflows/deploy-staging.yml`, `.github/workflows/staging-e2e-smoke.yml`

- [ ] **Production deployment readiness**
  - PM/lead go/no-go approval recorded in Progress Log
  - Incident response plan documented (rollback owner, escalation path)
  - Secrets Manager entries verified (Richpanel API key, Shopify credentials, OpenAI API key)
  - Change window identified (date/time, notification sent to stakeholders)
  - **Reference:** `docs/09_Deployment_Operations/Production_Deployment_Checklist.md`

### Post-Deployment Validation

- [ ] **Production E2E smoke test passed**
  - Prod smoke run URL captured
  - DynamoDB evidence (idempotency/state/audit records) confirmed
  - CloudWatch Logs show routing + reply evidence
  - **No customer impact** (test ticket used, or synthetic event with opt-in customer)
  - **Reference:** `.github/workflows/prod-e2e-smoke.yml`

- [ ] **Monitoring + alerting verified in production**
  - CloudWatch dashboard live and showing metrics
  - Alarms configured and tested (trigger test alarm, confirm notification)
  - Log retention policy set (7-30 days recommended)
  - **Reference:** `docs/08_Observability_Analytics/Logging_Metrics_Tracing.md`

---

### Completion Criteria

Order Status is considered **deployment-ready** when:

1. All E2E proofs (tracking + no-tracking + follow-up) are PASS_STRONG
2. Read-only shadow mode validation completed (zero writes confirmed)
3. CI gates passing (CI checks, Codecov, Bugbot)
4. Staging deployment + smoke tests green
5. PM/lead go/no-go approval recorded
6. Production deployment succeeded + prod smoke test passed
7. Post-deployment monitoring verified (alarms, logs, dashboards)

**Do not deploy to production until all checklist items are complete.**

---

Notes:
- Build owners can be adjusted as build mode progresses.
- Keep this file small; detailed tasks belong in `PLAN_CHECKLIST.md` and source docs.
- Do not claim dev/staging/prod state here unless linked to verified evidence.
