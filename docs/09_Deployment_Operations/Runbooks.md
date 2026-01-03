# Runbooks

Last updated: 2025-12-29

Central index for operational runbooks.

---

## 0) Purpose

Runbooks are used to respond to incidents and operational issues quickly, with minimal ambiguity.

Canonical runbooks live here:
- `docs/10_Operations_Runbooks_Training/runbooks/`

---

## 1) Runbook catalog

| ID | Title | File |
|---|---|---|
| R001 | Webhook Failures and Duplicate Storms | [R001_Webhook_Failures_and_Duplicate_Storms.md](10_Operations_Runbooks_Training/runbooks/R001_Webhook_Failures_and_Duplicate_Storms.md) |
| R002 | Misrouting Spike | [R002_Misrouting_Spike.md](10_Operations_Runbooks_Training/runbooks/R002_Misrouting_Spike.md) |
| R003 | Automation Wrong Reply or PII Risk | [R003_Automation_Wrong_Reply_or_PII_Risk.md](10_Operations_Runbooks_Training/runbooks/R003_Automation_Wrong_Reply_or_PII_Risk.md) |
| R004 | Vendor Rate Limit Storm | [R004_Vendor_Rate_Limit_Storm.md](10_Operations_Runbooks_Training/runbooks/R004_Vendor_Rate_Limit_Storm.md) |
| R005 | Backlog Catchup and DLQ | [R005_Backlog_Catchup_and_DLQ.md](10_Operations_Runbooks_Training/runbooks/R005_Backlog_Catchup_and_DLQ.md) |
| R006 | Cost Spike Token Runaway | [R006_Cost_Spike_Token_Runaway.md](10_Operations_Runbooks_Training/runbooks/R006_Cost_Spike_Token_Runaway.md) |
| R007 | Order Status Automation Failure | [R007_Order_Status_Automation_Failure.md](10_Operations_Runbooks_Training/runbooks/R007_Order_Status_Automation_Failure.md) |
| R008 | Chargebacks Disputes Process | [R008_Chargebacks_Disputes_Process.md](10_Operations_Runbooks_Training/runbooks/R008_Chargebacks_Disputes_Process.md) |
| R009 | Shipping Exceptions Returns Workflow | [R009_Shipping_Exceptions_Returns_Workflow.md](10_Operations_Runbooks_Training/runbooks/R009_Shipping_Exceptions_Returns_Workflow.md) |
| R010 | Prompt or Template Change Release | [R010_Prompt_or_Template_Change_Release.md](10_Operations_Runbooks_Training/runbooks/R010_Prompt_or_Template_Change_Release.md) |

---

## 1A) Operator playbook (first five minutes)
- Alerts to expect: `rp-mw-<env>-dlq-depth`, `rp-mw-<env>-worker-errors`, `rp-mw-<env>-worker-throttles`, `rp-mw-<env>-ingress-errors`.
- First look: CloudWatch Dashboard `${rp-mw-<env>-ops}` (added by CDK) — check DLQ depth, worker errors/throttles, ingress errors.
- Logs: CloudWatch Logs Insights on `/aws/lambda/rp-mw-<env>-ingress` or `/aws/lambda/rp-mw-<env>-worker`; filter on `event` and `event_id` fields (structured logging envelope).
- Contain: if errors persist, set `/rp-mw/<env>/safe_mode=true` or `/rp-mw/<env>/automation_enabled=false` (SSM parameters) to force route-only.
- Then pivot to the specific runbook: DLQ/backlog → `R005`; ingress auth/schema issues → `R001`; vendor/routing errors → `R004`/`R003` as applicable.

---

## 2) Runbook structure standard

Every runbook should include:
- **Symptoms / alerts**
- **Immediate containment** steps
- **Diagnosis** steps (what to check)
- **Mitigation** steps (safe to run repeatedly)
- **Rollback / recovery** (if applicable)
- **Post-incident follow-ups** (what to improve)

---

## 3) Change protocol

- If you add a new runbook, update this file and regenerate registries:
  - `python scripts/regen_doc_registry.py`
- If a runbook materially changes, add a note to `docs/00_Project_Admin/Change_Log.md`.
