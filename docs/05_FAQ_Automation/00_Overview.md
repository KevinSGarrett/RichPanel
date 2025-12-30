# Wave 05 — FAQ Automation (Copy, Macros, and Safe Reply Playbooks)

Last updated: 2025-12-29  
Status: **Complete ✅ (Wave 05 closeout)**

## What Wave 05 covers

## Locked v1 defaults (selected to unblock implementation)
- Auto-send enabled on: **LiveChat + Email**
- Route-only on: **Social/TikTok/Phone**
- Sender identity: **Support** (not “Bot”)
- No “Automated update:” label by default
- Policy links disabled by default (populate brand constants to enable)

See: `Automation_Sender_Identity_and_Channel_Scope.md`

Wave 05 turns the “template_id-only” automation interface from Wave 04 into a **production-ready FAQ automation library**:

1) **Customer-facing copy library**  
   - Approved message templates per `template_id`
   - Channel-aware variants (email vs live chat vs SMS) where needed  
   - A clear brand tone guide and “do/don’t” rules

2) **Order status automation (Tier 2 verified)**  
   - Safe order matching rules (avoid wrong-order privacy leaks)
   - What order fields are allowed to be disclosed (and what is disallowed)
   - Tracking link/number response patterns
   - Conservative fallbacks when data is missing or ambiguous

3) **Structured intake automations (Tier 1)**  
   For high-effort issues (missing items, damaged items, troubleshooting), we automate **intake** (collecting key info) but always route to a human.

4) **Macros alignment + governance**  
   - Identify existing Richpanel macros that should be reused or cleaned up
   - Define a “source of truth” policy so macros/templates do not drift
   - Naming conventions for automation-safe macros (recommended prefix: `AUTO:`)

5) **Safety and reliability constraints specific to auto-replies**  
   - De-duplication and loop prevention
   - Rate limiting (per ticket / per customer / global)
   - Auto-close only for explicitly whitelisted, deflection-safe templates (CR-001 adds an order-status ETA exception). Never pretend a human performed an action

## Inputs for this wave
- Top FAQ volume summary from `RoughDraft/Top_10_FAQ.txt` (order status & tracking is ~52% of tickets).
- Current Richpanel macro exports (from Richpanel docs library → `04_SETUP_CONFIGURATION/current-setup/macros/`).
- Common issues references (esp. `10-order-status-pitfalls.md`).

## Outputs for this wave
Primary deliverables:
- `Templates_Library_v1.md` + `templates/templates_v1.yaml`
- Updated playbooks and tone guide:
  - `Order_Status_Automation.md`
  - `Top_FAQs_Playbooks.md`
  - `Response_Templates_and_Tone.md`
  - `Human_Handoff_and_Escalation.md`
- Macro alignment plan:
  - `Macro_Alignment_and_Governance.md`
- Automation safeguards:
  - `FAQ_Automation_Dedup_Rate_Limits.md`

## Non-goals (explicit)
- We are **not** implementing production code here.
- Tier 3 “auto-actions” remain disabled (early rollout safety posture).


---

## New in Wave 05 Update 2
To support closeout and governance, Wave 05 now also includes:
- Brand constants + policy links:
  - `templates/brand_constants_v1.yaml`
  - `Brand_Constants_and_Policy_Links.md`
- Stakeholder approval pack:
  - `Stakeholder_Review_and_Approval.md`
  - `review/Template_Review_Checklist.csv`
- Richpanel AUTO macro alignment pack:
  - `Richpanel_AUTO_Macro_Setup_Checklist.md`
  - `Richpanel_AUTO_Macro_Pack_v1.md`
  - `templates/richpanel_auto_macro_mapping_v1.csv`
- Sender identity + channel scope recommendation:
  - `Automation_Sender_Identity_and_Channel_Scope.md`
- QA test cases for Wave 09:
  - `FAQ_Playbook_Test_Cases.md`
