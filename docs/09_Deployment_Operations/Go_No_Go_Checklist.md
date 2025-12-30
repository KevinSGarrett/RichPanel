# Go / No-Go Checklist (Release Readiness)

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

This checklist is the **final gate** before:
- any production deployment, and/or
- enabling any customer-facing automation in production.

**Rule:** If any safety/privacy item fails → **NO-GO** (no exceptions).

---

## A) Testing gates
- [ ] Unit + component tests passing (CI)
- [ ] Contract tests passing (webhook input schema, LLM output schema, observability event schema)
- [ ] Integration tests passing (stubbed vendors at minimum)
- [ ] LLM regression gates passing **if** prompt/template/model/schema changed
- [ ] Smoke test pack executed (routing baseline) and evidence captured
- [ ] Smoke test pack executed for Tier 1 automation subset **if** enabling automation
- [ ] Load/soak tests completed for major throughput changes (recommended)

Refs:
- `docs/08_Testing_Quality/Test_Strategy_and_Matrix.md`
- `docs/08_Testing_Quality/Contract_Tests_and_Schema_Validation.md`
- `docs/08_Testing_Quality/Integration_Test_Plan.md`
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/Load_and_Soak_Testing.md`

---

## B) Security + privacy gates
- [ ] Webhook authentication configured (or safe fallback documented)
- [ ] Secrets stored in Secrets Manager (no plaintext in repo)
- [ ] Logs are redacted; no raw message bodies persisted
- [ ] Kill switch verified end-to-end:
  - [ ] `automation_enabled=false` stops replies
  - [ ] `safe_mode=true` forces route-only
- [ ] Incident runbooks exist and are reachable (key leak, webhook abuse, PII leak)

Refs:
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- `docs/06_Security_Privacy_Compliance/Incident_Response_Security_Runbooks.md`

---

## C) Reliability gates
- [ ] API Gateway + Lambda health alarms configured
- [ ] SQS backlog + DLQ alarms configured
- [ ] Parameter defaults applied (concurrency caps, retry caps)
- [ ] Degraded mode playbook reviewed and owner assigned

Refs:
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

---

## D) Observability gates
- [ ] Dashboards exist (health + quality + cost)
- [ ] Correlation IDs present end-to-end
- [ ] Alerts route to the correct owner
- [ ] Operator quick-start runbook is accessible

Refs:
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
- `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`

---

## E) Business/ops readiness
- [ ] Chargebacks/Disputes queue exists and is staffed
- [ ] Returns Admin knows missing-items/DNR process (claims)
- [ ] Macros/templates are aligned (Wave 05) **if** you also maintain Richpanel macros
- [ ] Escalation path defined (Leadership Team)

Refs:
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- `docs/05_FAQ_Automation/Macro_Alignment_and_Governance.md`

---

## F) Rollback readiness
- [ ] Configuration rollback tested:
  - set `automation_enabled=false`
  - set `safe_mode=true`
- [ ] Template-level disablement tested (disable one template_id safely)
- [ ] Previous version deploy path exists
- [ ] Rollback triggers and owner assigned

Refs:
- `docs/09_Deployment_Operations/Release_and_Rollback.md`
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

---

## G) Release runbook
- [ ] Release driver has read and will follow the runbook
- [ ] Observer assigned for the first 60–120 minutes
- [ ] Stakeholders notified

Refs:
- `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`

---

## Final decision
- **GO** if all required items are checked.
- **NO-GO** if any safety/privacy item fails (no exceptions).
