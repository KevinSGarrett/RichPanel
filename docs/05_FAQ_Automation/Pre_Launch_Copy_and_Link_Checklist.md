# Pre-Launch Copy and Link Checklist (Wave 05 output)

Last updated: 2025-12-22  
Status: Final

## Purpose
Wave 05 defines the **template library** and playbooks. This checklist ensures you do not ship
customer-facing automation with placeholders, broken links, or unapproved language.

This checklist is designed to be used during:
- Wave 09 (release readiness)
- any subsequent template/macro changes

---

## A) Brand constants
File: `docs/05_FAQ_Automation/templates/brand_constants_v1.yaml`

- [ ] `support_signature` is set to your preferred signature (example: “{Brand} Customer Support”)
- [ ] `support_hours_text` (optional) is correct or empty
- [ ] Any URLs you populate are correct, public, and tested:
  - [ ] help center
  - [ ] returns policy
  - [ ] shipping policy
  - [ ] privacy policy
  - [ ] warranty policy
  - [ ] order-status portal (if applicable)

---

## B) Template copy review (minimum)
File: `docs/05_FAQ_Automation/review/Template_Review_Checklist.csv`

For each template that is enabled in v1:
- [ ] Tone matches your brand
- [ ] No promises that violate policy (“refund/reship guaranteed”, “we will cancel immediately”, etc.)
- [ ] No sensitive disclosures without verification (order details only in Tier 2 verified templates)
- [ ] Includes a clear handoff path (“reply here and we’ll help”)

---

## C) Formatting and channel sanity checks
- [ ] LiveChat templates are short and readable on mobile
- [ ] Email templates include signature and do not include broken formatting
- [ ] Links (if used) are not “naked long URLs” when possible

---

## D) Rollout guardrails
- [ ] “Auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)” confirmed in Richpanel automations/config (no conflicting rules)
- [ ] De-dup window and max auto-replies per ticket are configured (see `FAQ_Automation_Dedup_Rate_Limits.md`)
- [ ] Monitoring is enabled for:
  - auto-reply volume
  - Tier 0 misfires
  - Tier 2 verifier failures
  - delivery failures / API 429s

---

## E) Sign-off record
Record sign-off in:
- `docs/00_Project_Admin/Decision_Log.md`
- and attach the completed CSV checklist to your internal ticket/PR
