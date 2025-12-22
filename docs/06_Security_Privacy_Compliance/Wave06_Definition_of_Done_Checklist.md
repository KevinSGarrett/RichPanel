# Wave 06 — Definition of Done Checklist

Last updated: 2025-12-22

This checklist defines when Wave 06 (Security / Privacy / Compliance) is considered **complete** at the documentation level.

> Important: some items are **go-live gates** (must be verified before production rollout), but they do not block completing the documentation wave.

---

## A) Documentation deliverables complete (Wave 06 completion gate)

### Core security/privacy docs
- [ ] `Security_Privacy_Compliance_Overview.md` is complete and reflects current architecture
- [ ] `Data_Classification_and_PII_Inventory.md` is complete
- [ ] `PII_Handling_and_Redaction.md` is complete (no raw PII logging; fail-closed policy)
- [ ] `Data_Retention_and_Access.md` is complete (TTL + deletion path)
- [ ] `Webhook_Auth_and_Request_Validation.md` is complete (auth options + validation rules)
- [ ] `Secrets_and_Key_Management.md` is complete (Secrets Manager + rotation posture)
- [ ] `IAM_Least_Privilege.md` is complete (role separation + least privilege)
- [ ] `Network_Security_and_Egress_Controls.md` is complete (rate limiting + SSRF protection)
- [ ] `Encryption_and_Data_Protection.md` is complete (TLS + at-rest encryption posture)
- [ ] `Vendor_Data_Handling_OpenAI_Richpanel_Shopify.md` is complete
- [ ] `Threat_Model_STRIDE.md` is complete
- [ ] `Security_Controls_Matrix.md` maps threats → controls → verification
- [ ] `Secure_SDLC_and_Security_Testing.md` defines security test minimums
- [ ] `Incident_Response_Security_Runbooks.md` covers key incident types

### Operational safety docs (Wave 06 Update 2+)
- [ ] `AWS_Security_Baseline_Checklist.md` exists + CSV checklist exists
- [ ] `Kill_Switch_and_Safe_Mode.md` exists + defines runtime flags
- [ ] `Security_Monitoring_Alarms_and_Dashboards.md` exists (minimum alarms + dashboards)
- [ ] `Webhook_Secret_Rotation_Runbook.md` exists (no-downtime rotation)
- [ ] `IAM_Access_Review_and_Break_Glass.md` exists (cadence + break-glass)

### Admin hygiene
- [ ] `Progress_Wave_Schedule.md` updated (Wave 06 status)
- [ ] `Decision_Log.md` updated (Wave 06 decisions)
- [ ] `Risk_Register.md` updated (Wave 06 mitigations)
- [ ] `Change_Log.md` updated (Wave 06 Update 3 entry)
- [ ] `INDEX.md` + `REGISTRY.md` include all Wave 06 docs

---

## B) Minimum “implementation prerequisites” captured (not necessarily executed)

- [ ] Secrets identified (Richpanel key, webhook token, OpenAI key, Shopify key if used)
- [ ] Roles defined (ingress vs worker)
- [ ] Recommended retention/TTL documented
- [ ] Kill switch plan documented and easy to execute
- [ ] Alarm list documented with runbooks

---

## C) Go-live verification items (must be verified before production rollout)

These can remain **deferred** during planning but must be verified before go-live:
- [ ] Confirm which webhook auth transport works in your Richpanel tenant:
  - custom headers vs body token vs URL token
- [ ] Confirm any company-specific compliance constraints (retention windows, required disclosures)
- [ ] Confirm OpenAI org settings / data controls posture for production use (at minimum: do not store request/response bodies in app logs)

---

## D) Wave 06 closeout decision
- [ ] Wave 06 marked **Complete ✅** in `Progress_Wave_Schedule.md`
- [ ] Any unresolved go-live items are tracked in `Open_Questions.md` with owners

