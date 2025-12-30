# Compliance Readiness Checklist (v1)

Last updated: 2025-12-22

This is a lightweight compliance checklist for a customer support automation middleware.

**Goal:** be “compliance-ready” without over-engineering v1.

---

## 1) Privacy principles (baseline)
- data minimization (send/store only what is required)
- purpose limitation (support operations only)
- least privilege access
- retention limits and deletion workflows
- vendor review (OpenAI/Richpanel/Shopify)

---

## 2) US privacy (CCPA/CPRA) readiness
Even if not formally audited, we should be able to:
- identify where customer data flows
- honor deletion requests for any stored data we control
- provide transparency about automated support where required by policy

---

## 3) GDPR (if applicable)
If you have EU customers (or choose to be future-proof), plan for:
- lawful basis for processing (support contract / legitimate interest)
- data subject access requests (DSAR)
- deletion requests (right to erasure)
- vendor DPAs and subprocessor lists

---

## 4) What we must document for “auditability”
- data inventory + classification (this wave)
- retention periods + access controls
- incident response runbooks
- change management for:
  - templates/macros
  - routing taxonomy
  - model/prompt versions

---

## 5) What we must avoid in v1
- Storing raw conversation logs indefinitely
- Logging PII to centralized systems without redaction
- Auto-resolving sensitive issues (chargebacks/disputes/fraud)
- Disclosing order info without deterministic match

---

## 6) “Compliance ready” deliverables (Wave 06)
- Data inventory doc complete
- Retention doc complete (with TTLs + log retention)
- Security controls matrix complete
- Incident response runbooks complete
- Vendor handling doc complete (OpenAI data controls documented)

