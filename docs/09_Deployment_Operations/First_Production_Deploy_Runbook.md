# First Production Deploy Runbook (v1)

Last updated: 2025-12-22  
Scope: Wave 09 — Release readiness (**step-by-step runbook**)

This runbook is the **copy/paste style** procedure for the *first* production deploy of the middleware.

It assumes the recommended release principle:
1) deploy **routing-only** first  
2) enable limited **Tier 1** automation  
3) enable **Tier 2 verified** order status only after deterministic match is proven

This runbook intentionally emphasizes **safety levers**:
- `automation_enabled=false` stops all customer-facing auto-replies
- `safe_mode=true` forces route-only
- template-level disables allow surgical rollback

Refs:
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
- `docs/09_Deployment_Operations/Release_and_Rollback.md`

---

## 0) Roles (minimum)
Before starting, assign:

- **Release driver (single person)** — executes checklist end-to-end
- **Observer** — watches dashboards/logs and confirms health
- **Support Ops point** — validates routing/assignment behavior in Richpanel
- **Rollback owner** — has authority to trigger kill switch immediately

---

## 1) Pre-deploy gates (must pass)
### 1.1 CI and testing
- [ ] Unit + contract tests pass
- [ ] LLM regression gates pass **if** prompts/templates/schemas changed
- [ ] Manual QA checklist A+B completed in staging
- [ ] Smoke test pack baseline cases reviewed (routing-only)

Refs:
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`
- `docs/08_Testing_Quality/Manual_QA_Checklists.md`
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`

### 1.2 Security and secrets
- [ ] Webhook auth mechanism chosen (header token preferred; fallback documented)
- [ ] Secrets exist for prod (Richpanel token, OpenAI key, webhook token)
- [ ] Secrets are stored in Secrets Manager (no plaintext)

Refs:
- `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`
- `docs/06_Security_Privacy_Compliance/Secrets_and_Key_Management.md`

### 1.3 Observability and alarms
- [ ] Dashboards exist (health + quality + cost)
- [ ] Critical alarms exist (API errors, DLQ, queue age, throttles)
- [ ] Log redaction confirmed (no raw message bodies)

Refs:
- `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`

### 1.4 Feature flags default (prod-safe)
Set initial prod config:
- `automation_enabled=false`
- `safe_mode=true`
- template whitelist empty (or all templates disabled)

This ensures the first deploy is **routing-only**.

---

## 2) Production deployment (routing-only)

### 2.1 Deploy
Deploy the new version to production (IaC / CI-CD pipeline).  
Ensure the applied defaults match:
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

### 2.2 Validate “pipeline alive”
Perform 2–3 controlled test tickets:
- one Sales inquiry
- one Returns issue
- one Technical Support issue

Expect:
- ingress success (2xx)
- message enqueued and processed
- tags applied and team routing performed
- **no auto-replies** (safe_mode + automation_enabled)

### 2.3 Observe for 60 minutes (minimum)
Watch:
- queue depth / oldest message age
- error rates
- DLQ
- vendor 429 spikes
- cost signals (tokens/requests)

If any critical issue occurs:
- trigger rollback immediately (Section 6)

---

## 3) Enable limited Tier 1 automation (safe-assist)
Only proceed if:
- routing-only phase is stable
- no PII/logging incidents
- Support Ops confirms routing looks correct

### 3.1 Enable automation in a controlled way
Recommended order:

1) Set `safe_mode=false`
2) Set `automation_enabled=true`
3) Enable **only** Tier 1 templates that are safest:
   - `t_order_status_ask_order_number`
   - `t_delivered_not_received_intake`
   - `t_missing_items_intake`
   *(optional)* `t_technical_support_intake`

Do **not** enable Tier 2 templates yet.

### 3.2 Run Tier 1 smoke subset
Run the Tier 1 rows in:
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Capture evidence for go/no-go.

---

## 4) Enable Tier 2 verified order status (optional, later)
Only proceed if:
- deterministic match is proven in production (linked orders available)
- Tier 2 verifier is in place (if used)
- no mis-disclosure incidents in Tier 1 phase

### 4.1 Enable Tier 2 templates
Enable:
- `t_order_status_verified`
- `t_shipping_delay_verified` *(optional, if shipping-delay matching works)*

### 4.2 Run Tier 2 smoke subset
Run ST-040 / ST-041 style tests:
- match and no-match cases
- confirm **no disclosure** without deterministic match

---

## 5) Post-release monitoring (first 24 hours)
- Watch the same health metrics as routing-only
- Add daily review of:
  - policy_override rate
  - Tier 0 volume
  - automation send count
  - customer dissatisfaction signals (if available)

Refs:
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
- `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`

---

## 6) Rollback / emergency actions (fastest first)
### 6.1 Immediate stop of customer-facing automation
- set `automation_enabled=false`
- set `safe_mode=true`

### 6.2 Surgical disablement (template-level)
Disable the specific `template_id` that is misbehaving.

### 6.3 Revert deployment
Deploy the previous version (only if config rollback is insufficient).

Refs:
- `docs/09_Deployment_Operations/Release_and_Rollback.md`

---

## 7) Post-incident or post-rollout follow-up
Any rollback or near-miss requires:
- incident note (what happened, when, what was changed)
- Decision Log entry (if defaults changed)
- update to:
  - `Risk_Register.md`
  - `Adversarial_and_Edge_Case_Test_Suite.md` (if applicable)
  - Golden set (if new failure pattern discovered)
