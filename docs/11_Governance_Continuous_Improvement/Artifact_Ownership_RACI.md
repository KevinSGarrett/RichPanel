# Artifact Ownership and RACI

Last updated: 2025-12-22

This document defines **who owns what** so nothing becomes “everyone’s job” (and therefore nobody’s job).

---

## Roles (recommended defaults)

> You can rename roles to match your org; keep the responsibilities.

- **Engineering Owner (EO):** owns code behavior, reliability, rollout/rollback
- **Support Ops Owner (SO):** owns customer-facing copy, macros, and routing “business meaning”
- **Quality/Eval Owner (QO):** owns evaluation sets, labeling workflow, weekly quality triage
- **Security/Privacy Reviewer (SP):** reviews auth/logging/PII exposure changes
- **Leadership Approver (LA):** approval for major policy changes, risk acceptance

---

## RACI table (v1)

| Artifact / Decision | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Prompt updates | EO | EO | QO, SP | SO, LA |
| Threshold changes | QO | EO | SO | LA |
| Taxonomy changes | QO | SO | EO | LA |
| Template copy changes | SO | SO | QO | EO, LA |
| Template enable/disable | EO | EO | SO | LA |
| New template_id | SO | SO | EO, QO | LA |
| Routing mapping to teams | SO | SO | EO | LA |
| Webhook auth / secrets | EO | EO | SP | LA |
| Logging/retention changes | EO | EO | SP | LA |
| Vendor model change | EO | EO | QO, SO, SP | LA |
| Incident response runbooks | EO | EO | SO, SP | LA |

---

## Decision logging requirements
Any decision that changes:
- customer-facing behavior
- data exposure risk
- automation eligibility
must be recorded in `Decision_Log.md`.

