# Wave 06 — Security, Privacy, and Compliance

Last updated: 2025-12-22  
Status: **Complete** ✅ (documentation complete; go-live verification items tracked)

## Goals
Make the middleware production-safe with respect to:
- customer PII (email/phone/order #/tracking)
- webhook spoofing/abuse and automation loops
- credential/secrets management
- least privilege access and environment separation
- retention/deletion and compliance readiness
- operational safety controls (kill switch / safe mode)
- minimum monitoring/alerting for security + privacy signals

---

## Deliverables (Wave 06)

### Core docs (source of truth)
- `docs/06_Security_Privacy_Compliance/Security_Privacy_Compliance_Overview.md`
- `docs/06_Security_Privacy_Compliance/Data_Classification_and_PII_Inventory.md`
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`
- `docs/06_Security_Privacy_Compliance/Data_Retention_and_Access.md`
- `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`
- `docs/06_Security_Privacy_Compliance/Secrets_and_Key_Management.md`
- `docs/06_Security_Privacy_Compliance/IAM_Least_Privilege.md`
- `docs/06_Security_Privacy_Compliance/Network_Security_and_Egress_Controls.md`
- `docs/06_Security_Privacy_Compliance/Encryption_and_Data_Protection.md`
- `docs/06_Security_Privacy_Compliance/Vendor_Data_Handling_OpenAI_Richpanel_Shopify.md`
- `docs/06_Security_Privacy_Compliance/Threat_Model_STRIDE.md`
- `docs/06_Security_Privacy_Compliance/Security_Controls_Matrix.md`
- `docs/06_Security_Privacy_Compliance/Secure_SDLC_and_Security_Testing.md`
- `docs/06_Security_Privacy_Compliance/Incident_Response_Security_Runbooks.md`
- `docs/06_Security_Privacy_Compliance/Compliance_Readiness_Checklist.md`

### AWS baseline + operational controls
- `docs/06_Security_Privacy_Compliance/AWS_Security_Baseline_Checklist.md` (+ CSV)
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- `docs/06_Security_Privacy_Compliance/Webhook_Secret_Rotation_Runbook.md`
- `docs/06_Security_Privacy_Compliance/IAM_Access_Review_and_Break_Glass.md`

### Completion checklist (this wave)
- `docs/06_Security_Privacy_Compliance/Wave06_Definition_of_Done_Checklist.md`

---

## Key decisions locked (Wave 06)
- Secrets stored in **AWS Secrets Manager** (no secrets in repos/logs)
- PII-safe logging: **no raw message bodies stored by default**
- Automation safety: **fail closed** (route-only) on policy/schema/auth failures
- Kill switch / safe mode supported via runtime flags
- Minimum alarms/dashboards defined (security baseline)

---

## Deferred go-live verification items (tracked; not blocking docs completion)
These must be verified before production rollout:
- Confirm which webhook auth transport works in your Richpanel tenant (custom header vs body token vs URL token)
- Confirm any company-specific compliance constraints (retention, required disclosures)
- Confirm production OpenAI data-controls posture (at minimum: do not store request/response bodies in app logs)

These items remain tracked in:
- `docs/00_Project_Admin/Open_Questions.md`
- `docs/06_Security_Privacy_Compliance/Wave06_Definition_of_Done_Checklist.md`

---

## Hand-off to Wave 07
Wave 07 (Reliability/Scaling) should:
- translate alarms into concrete CloudWatch templates/IaC (if desired)
- finalize backpressure, retries, and concurrency limits under real traffic
- expand SLOs and cost guardrails
