# Stakeholder Review and Approval (Wave 05)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout process)**

## Purpose
Wave 05 introduces **customer-facing copy** that can be used for automated replies.

Even if you proceed with implementation immediately, **a copy/policy review must occur before production rollout** to ensure:
- policy promises are accurate (returns/refunds/shipments)
- tone matches your brand
- disclosures are safe and consistent
- escalation/handoff language is correct

This file defines the **review process**; it does not require you to complete approvals now.

Checklist CSV:
- `review/Template_Review_Checklist.csv`

Human-readable library:
- `Templates_Library_v1.md`

---

## What is considered “approved” for implementation vs production
### Implementation-ready baseline (this repo)
- Templates are drafted and consistent
- Variables and channel variants are defined
- Tier gates + playbooks prevent unsafe sends

### Production-ready sign-off (required before go-live)
- Template review checklist completed (CSV)
- Brand constants populated (signature + links if used)
- Any policy-linked copy verified by Support Ops / Leadership
- Decision log updated with “approved for production” decision

---

## Review steps (recommended)
### A) Brand constants
File: `templates/brand_constants_v1.yaml`

Confirm:
- support signature is correct
- optional hours text is correct or empty
- any URLs you add are correct and public

### B) Template copy
File: `review/Template_Review_Checklist.csv` + `Templates_Library_v1.md`

For each enabled template confirm:
- tone is acceptable
- no policy promises or commitments beyond what you allow
- does not disclose sensitive info without verification (Tier 2 only)
- includes a clear “reply here” escape hatch

### C) Automation scope and restrictions
Files: `Top_FAQs_Playbooks.md` and `Order_Status_Automation.md`

Confirm:
- Tier 2 only for order/tracking disclosures
- never auto-close
- no refunds/reships promised automatically in v1

---

## Recording approvals
When approvals are complete, record in:
- `docs/00_Project_Admin/Decision_Log.md`
- and attach the completed CSV to your internal ticket/PR

See also: `docs/05_FAQ_Automation/Pre_Launch_Copy_and_Link_Checklist.md`
