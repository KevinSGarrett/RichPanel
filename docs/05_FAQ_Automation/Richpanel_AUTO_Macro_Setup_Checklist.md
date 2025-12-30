# Richpanel AUTO Macro Setup Checklist (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Create a dedicated set of **automation-aligned** macros in Richpanel so:
- agents can reply consistently with automation wording
- supervisors can audit wording easily
- we reduce copy drift over time

**Source of truth:** middleware templates in `templates/templates_v1.yaml`  
**Macro mapping file:** `templates/richpanel_auto_macro_mapping_v1.csv`

> Note: The middleware does **not** require Richpanel macros to send automated replies.
> Macros are primarily for **agent consistency** and governance.

---

## Recommended macro naming convention
Prefix all automation-aligned macros with:
- `AUTO:`

Example:
- `AUTO: Order Status — Ask for Order #`
- `AUTO: Missing Items — Intake`

This makes it obvious in the UI which macros are aligned to automation.

---

## Setup steps (copy/paste workflow)
1) Export (or view) current macros list in Richpanel (for baseline)
2) Create a new macro category/folder called: **AUTO (Middleware-aligned)**
3) For each row in `richpanel_auto_macro_mapping_v1.csv`:
   - Create a macro with the `suggested_macro_name`
   - Paste the copy from the **template library**
     - If you want Richpanel placeholders (like customer first name), replace Mustache placeholders with the Richpanel equivalents available in your workspace.
4) Ensure these macros are visible to the right agent groups
5) Record completion in `docs/00_Project_Admin/Decision_Log.md`:
   - “AUTO macro set created (v1) — date — owner”

---

## Placeholder compatibility (important)
Middleware templates use **Mustache** (e.g., `{{first_name}}`).  
Richpanel macros may use a different placeholder system (example seen in your current macros):
- `%First Name%`
- `%Order Name%`
- `%Order Tracking URL%`

Because placeholder systems differ, the safest approach is:
- Keep Richpanel AUTO macros mostly **static** (intake templates are best)
- Avoid complex dynamic fields unless you have confirmed the exact Richpanel placeholder names

---

## Minimum macro set (recommended for early rollout)
If you don’t want to create all macros yet, start with the Tier 1 intake set:
- `t_order_status_ask_order_number`
- `t_delivered_not_received_intake`
- `t_missing_items_intake`
- `t_wrong_item_intake`
- `t_damaged_item_intake`
- `t_return_request_intake`
- `t_exchange_request_intake`
- `t_refund_request_intake`
- `t_technical_support_intake`

These are high ROI and mostly static (low risk of placeholder mismatch).

---

## Drift prevention
- Re-export macros monthly (or after major policy changes)
- Diff against the template library
- If drift is found:
  - update templates (preferred)
  - then update AUTO macros to match
