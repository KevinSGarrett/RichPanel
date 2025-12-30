# Open Questions

## CR-001 — No-tracking delivery estimates (Order Status)

1) What are the exact `shipping_method_name` strings from Shopify/Richpanel that map to:
   - Standard (3–5 business days)
   - Rushed (24 business hours)
   - Priority (24 business hours)
   - Pre-Order (variable)

2) Pre-orders: what is the source-of-truth for the ETA?
   - preferred: `preorder_eta_business_days`
   - acceptable: tag/metafield encoding ship-by date or business-day ETA
   - if none: route to human

3) Business-day calendar: Mon–Fri only, or holiday-aware? If holiday-aware, which holiday set (US federal?) and which timezone?

4) Richpanel auto-close semantics: if we mark as **Resolved**, does a customer reply reopen automatically in your workflow?

---
Last updated: 2025-12-29 (Wave F12)

These are questions that could affect build decisions.
If answered elsewhere (plan docs), we link and treat the plan/decision log as canonical.

---

## Resolved (canonical)

- Department/queue list + intent taxonomy:
  - `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- Richpanel tag-driven routing + control tags + assignment rules:
  - `docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md`
- PII handling posture:
  - `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`
- Secrets manager:
  - AWS Secrets Manager
- Agents:
  - 3 Cursor agents (A/B/C) + PM; agents update docs every run; refactors allowed with guardrails
- Backend language (Lambda runtime):
  - Python 3.11
- Admin console framework (planned):
  - Next.js (TypeScript)
- Reporting timezone:
  - **UTC everywhere** for logs/metrics; convert at UI layer if needed

---

## GitHub workflow (resolved)

- **Main branch protection:** **enabled** (PR required; required status checks; no direct push)
- **Merge style:** **merge commit** (preserve run boundaries)
- **Execution mode:** **sequential default** (single `run/<RUN_ID>` branch; A → B → C)
- **Tooling:** GitHub CLI (`gh`) + auth token **available** for PR creation/merge and Actions inspection
- **Branch discipline:** max 1 run branch per run (parallel only if explicitly instructed; max 3 agent branches)

Canonical references:
- `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
- `docs/08_Engineering/Multi_Agent_GitOps_Playbook.md`
- `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`

## Remaining (non-blocking)

- None required to proceed with build activation.



---
