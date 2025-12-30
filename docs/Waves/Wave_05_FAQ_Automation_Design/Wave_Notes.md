# Wave 05 — FAQ Automation Design

Last updated: 2025-12-22  
Status: **Complete ✅**

## Objective
Finalize the FAQ automation layer (copy + playbooks + governance) so the implementation team can build without ambiguity.

Wave 05 focuses on:
- Order status/tracking automation (Tier 2 verified)
- Structured intake automations for other top FAQs (Tier 1)
- Template library (customer-facing copy)
- Macro alignment strategy (avoid drift)
- Approval workflow and QA test coverage for FAQ automation

---

## Deliverables completed
### Template library
- `docs/05_FAQ_Automation/Templates_Library_v1.md`
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- Channel variants finalized:
  - `default` (email + general)
  - `livechat` (short)

### Order status automation
- `docs/05_FAQ_Automation/Order_Status_Automation.md`

### Playbooks + tone
- `docs/05_FAQ_Automation/Top_FAQs_Playbooks.md`
- `docs/05_FAQ_Automation/Response_Templates_and_Tone.md`
- `docs/05_FAQ_Automation/Human_Handoff_and_Escalation.md`

### Macro alignment + governance
- `docs/05_FAQ_Automation/Macro_Alignment_and_Governance.md`
- `docs/05_FAQ_Automation/Richpanel_AUTO_Macro_Pack_v1.md`
- `docs/05_FAQ_Automation/Richpanel_AUTO_Macro_Setup_Checklist.md`
- `docs/05_FAQ_Automation/templates/richpanel_auto_macro_mapping_v1.csv`

### Guardrails + QA
- `docs/05_FAQ_Automation/FAQ_Automation_Dedup_Rate_Limits.md`
- `docs/05_FAQ_Automation/FAQ_Playbook_Test_Cases.md`
- `docs/05_FAQ_Automation/Customer_Experience_Metrics.md`

### Closeout process artifacts
- `docs/05_FAQ_Automation/templates/brand_constants_v1.yaml`
- `docs/05_FAQ_Automation/Brand_Constants_and_Policy_Links.md`
- `docs/05_FAQ_Automation/Stakeholder_Review_and_Approval.md`
- `docs/05_FAQ_Automation/Pre_Launch_Copy_and_Link_Checklist.md`
- `docs/05_FAQ_Automation/review/Template_Review_Checklist.csv`

---

## Wave 05 decisions (locked defaults)
These defaults are selected so implementation can proceed without additional stakeholder input.
Final production approvals are tracked via the review checklist and Decision Log.

- **Automation enabled channels (v1):** LiveChat + Email
- **Route-only channels (v1):** Social/TikTok/Phone
- **Sender identity:** Support (not “Bot”)
- **“Automated update:” label:** Disabled by default in v1
- **Policy links:** Disabled by default in v1 (URLs blank until you populate)

Recorded in:
- `docs/05_FAQ_Automation/Automation_Sender_Identity_and_Channel_Scope.md`
- `docs/00_Project_Admin/Decision_Log.md`

---

## Remaining items (not blockers, tracked for pre-launch)
- Populate `brand_constants_v1.yaml` with your preferred signature and any policy URLs
- Complete the template review checklist CSV before production rollout

These are tracked in:
- `docs/05_FAQ_Automation/Pre_Launch_Copy_and_Link_Checklist.md`

---

## Next wave
Wave 06 — Security, privacy, and compliance hardening.
