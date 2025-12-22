# Automation Sender Identity and Channel Scope (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Define:
- **who** the automated message appears to come from (identity/signature)
- **where** automation is enabled (channels)
- how we avoid customer confusion and escalation risk

This document intentionally selects defaults so Wave 05 can close without additional stakeholder input.

---

## Decisions (v1 defaults)
### Sender identity
**Decision:** Messages should appear as coming from **Support** (not “a bot”).  
- Rationale: keeps tone consistent with your existing support operations and reduces “automation friction”.
- Implementation: message text comes from the template library; the sender identity is whatever Richpanel uses for outbound agent/support replies.

### Transparency line
**Decision:** **Do NOT** prepend “Automated update:” in v1.  
Instead, templates should use neutral framing like “Here’s the latest update” or “Order update:”.
- Rationale: avoids drawing attention to automation while still being helpful.
- Safety: templates always include a “reply here and we’ll help” escape hatch.

(If you later want transparency, we can add a `{{automation_label}}` variable and enable it per-channel.)

### Signature
**Decision:**  
- **Email:** end with `— {{support_signature}}`  
- **LiveChat:** no signature (keep it short)

**Source of truth:** `docs/05_FAQ_Automation/templates/brand_constants_v1.yaml`

---

## Channel scope decisions (v1)
### Enabled channels
**Decision (v1):**
- **LiveChat:** automation enabled (Tier 1 + Tier 2 as allowed)
- **Email:** automation enabled (Tier 1 + Tier 2 as allowed)

### Disabled (route-only) channels
- **Social/TikTok/Phone:** route-only (no auto-send) until channel behavior is validated

Why:
- LiveChat + Email provide the highest ROI for reducing agent workload
- Social/TikTok often carries higher brand-voice variability and public-context risk
- Phone is not a suitable channel for “auto-send” replies

---

## Hard rules (non-negotiable)
- Never auto-close tickets
- Never send order/tracking details without deterministic match (Tier 2 gate)
- Never promise refunds/reships/discounts in v1
- Any “legal/chargeback/fraud/harassment” intent is Tier 0:
  - route to the correct team
  - optionally send a neutral acknowledgement only (no details)

---

## Where this is enforced
- Template eligibility rules: `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`
- Playbooks: `docs/05_FAQ_Automation/Top_FAQs_Playbooks.md`
- De-dup + rate limits: `docs/05_FAQ_Automation/FAQ_Automation_Dedup_Rate_Limits.md`
- Decision log entry: `docs/00_Project_Admin/Decision_Log.md`
