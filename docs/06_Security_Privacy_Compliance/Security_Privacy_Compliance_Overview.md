# Security, Privacy, and Compliance Overview (Wave 06)

Last updated: 2025-12-22

Wave 06 hardens the middleware plan so it can be operated safely in production with:
- customer PII in inbound messages (email, phone, order #, tracking link/number)
- third‑party dependencies (Richpanel, Shopify, OpenAI)
- automated outbound messages (FAQ automation)

This wave is **documentation-first**. It defines required controls, default configurations, and acceptance gates for “production-ready”.

---

## 1) Scope

### In scope
- Webhook security for inbound Richpanel → middleware triggers
- PII minimization + redaction (especially logs and LLM inputs)
- Secrets & key management (Richpanel, OpenAI, Shopify)
- AWS IAM least privilege and environment separation
- Encryption in transit + at rest
- Retention + deletion plan (state + logs + evaluation data)
- Vendor data handling (what we send to OpenAI / what we store)
- Minimum secure SDLC gates and security testing
- Incident response runbooks (key leak, webhook abuse, PII leak, wrong replies)
- **Kill switch / safe mode** controls to stop automation quickly

### Out of scope (for now)
- Formal certifications (SOC 2 / ISO 27001) — we design so certification is possible later
- Advanced DLP tooling (beyond redaction + minimization)
- Network firewalling / full egress allowlisting (optional later)

---

## 2) Non‑negotiable security principles (v1)

1) **Fail closed:** if uncertain or degraded → route-only.
2) **Minimize data:** send the minimum needed to vendors and logs.
3) **No raw PII in logs:** redact before logging (always).
4) **No secrets in code:** secrets live in Secrets Manager only.
5) **Defense in depth:** webhook auth + throttling + WAF (prod) + idempotency.
6) **Operational control:** kill switch can disable automation in minutes.

---

## 3) Data classification summary (v1)

- **Sensitive customer identifiers (treat as PII):**
  - email, phone number
  - order #, tracking #, tracking link
  - any address details (if present)
- **Allowed in automation responses (Tier 2 only):**
  - order status + tracking link/number *only if deterministic match*
- **Disallowed in v1 auto replies:**
  - full addresses
  - payment details
  - internal order notes

---

## 4) Production readiness acceptance gates (Wave 06 closeout)

Wave 06 is considered “complete” when the plan includes:
- Webhook authentication design with tenant-safe fallbacks
- A documented AWS security baseline checklist
- A kill switch / safe mode operational plan
- PII redaction and retention rules
- Threat model + controls matrix
- Incident runbooks that reference the kill switch

Wave 06 is considered “implementation-ready” when additionally:
- Tenant webhook auth choice is confirmed (header token vs HMAC)
- OpenAI org data controls are confirmed (store=false, retention posture)
- AWS accounts + IAM boundaries are actually set up (dev/staging/prod)

---

## 5) Related documents (source of truth)

### Core security docs (Wave 06)
- Webhook auth & request validation: `Webhook_Auth_and_Request_Validation.md`
- AWS baseline checklist: `AWS_Security_Baseline_Checklist.md`
- Kill switch / safe mode: `Kill_Switch_and_Safe_Mode.md`
- Secrets: `Secrets_and_Key_Management.md`
- IAM: `IAM_Least_Privilege.md`
- Network/egress controls: `Network_Security_and_Egress_Controls.md`
- Encryption: `Encryption_and_Data_Protection.md`
- PII policy + redaction: `PII_Handling_and_Redaction.md`
- Retention & access: `Data_Retention_and_Access.md`
- Vendor data handling: `Vendor_Data_Handling_OpenAI_Richpanel_Shopify.md`
- Threat model: `Threat_Model_STRIDE.md`
- Controls matrix: `Security_Controls_Matrix.md`
- Secure SDLC + security testing: `Secure_SDLC_and_Security_Testing.md`
- Incident runbooks: `Incident_Response_Security_Runbooks.md`

### Adjacent waves
- Reliability + rate limits: `../07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`
- LLM safety gates: `../04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- Release/rollback (feature flags): `../09_Deployment_Operations/Release_and_Rollback.md`
