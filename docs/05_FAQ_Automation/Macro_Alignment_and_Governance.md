# Macro Alignment and Governance (Richpanel ↔ Middleware)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Why this matters
You currently have a large set of Richpanel macros (181 in the exported snapshot).  
If the middleware auto-replies with copy that differs from what human agents use, customers will experience:
- inconsistent answers
- contradictory policies
- re-opened conversations
- loss of trust

Wave 05 sets a governance model so:
- the middleware templates are safe and consistent
- Richpanel macros stay aligned over time

---

## Recommended “source of truth”
**Source of truth = middleware templates file**  
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`

Richpanel macros are then treated as a **synced mirror** for human agents.

Why this is best:
- templates are versioned (git) and reviewed
- rollbacks are easy
- drift is detectable (diff exports)
- automation copy can be regression-tested

---

## Naming conventions

---

## Wave 05 artifacts (what to use)
Wave 05 provides the following files to keep automation copy and Richpanel macros aligned:

### Canonical (middleware)
- `templates/templates_v1.yaml` — canonical customer-facing copy
- `templates/brand_constants_v1.yaml` — brand name/signature/links

### Macro alignment (Richpanel)
- `Richpanel_AUTO_Macro_Setup_Checklist.md` — how to create the AUTO macro set
- `Richpanel_AUTO_Macro_Pack_v1.md` — copy/paste starter bodies (static-friendly)
- `templates/richpanel_auto_macro_mapping_v1.csv` — 1:1 mapping between `template_id` and suggested macro names

### Review/approval
- `Stakeholder_Review_and_Approval.md`
- `review/Template_Review_Checklist.csv`

**Rule:** If macro copy and template copy conflict, update the template library first, then refresh macros.

---

### Automation-safe macros (recommended)
Create a dedicated set of macros with a clear prefix so agents know they are aligned with automation:

- `AUTO: Order Status — Verified`
- `AUTO: Order Status — Ask Order #`
- `AUTO: Missing Items — Intake`
- `AUTO: Technical Support — Intake`
- etc.

### Existing macros
You already have macros like:
- `ORDERS: Tracking Request`
- `ORDERS: Contact Warehouse: Tracking Not Updated`
- `ORDER ISSUE : Wrong Item Received: STEP 1: Photo Request`
- `SUBSCRIPTION: How to cancel`
- `TROUBLESHOOTING: Damage & Defect: Video Request`

Some of these are good starting points, but several include:
- placeholders like “INSERT ADDRESS” / “XXXX”
- agent-only instructions
- inconsistent signatures

We should either:
- update them to match the Wave 05 templates, or
- keep them for internal/human workflows but add the `AUTO:` macro set as the canonical customer-facing copy.

---

## Alignment map (v1)
Below is the recommended mapping from `template_id` → `AUTO:` macro.

| template_id | Recommended AUTO macro name | Notes |
|---|---|---|
| t_order_status_verified | AUTO: Order Status — Verified | Matches Tier 2 verified template |
| t_shipping_delay_verified | AUTO: Shipping Delay — Verified | Conservative copy; no promises |
| t_order_status_ask_order_number | AUTO: Order Status — Ask Order # | Used when no linked order |
| t_delivered_not_received_intake | AUTO: Delivered Not Received — Intake | Checklist + request order # |
| t_missing_items_intake | AUTO: Missing Items — Intake | Photo + packing slip request |
| t_wrong_item_intake | AUTO: Wrong Item — Intake | Photo request |
| t_damaged_item_intake | AUTO: Damaged Item — Intake | Photo/video request |
| t_cancel_order_ack_intake | AUTO: Cancel Order — Intake | No promises |
| t_address_change_ack_intake | AUTO: Address Change — Intake | No promises |
| t_cancel_subscription_ack_intake | AUTO: Cancel Subscription — Intake | Gather email |
| t_billing_issue_intake | AUTO: Billing — Intake | Warn about sensitive info |
| t_return_request_intake | AUTO: Return — Intake | |
| t_exchange_request_intake | AUTO: Exchange — Intake | |
| t_refund_request_intake | AUTO: Refund Status — Intake | |
| t_technical_support_intake | AUTO: Technical Support — Intake | |
| t_promo_discount_info | AUTO: Promo Code Help | No code generation |
| t_pre_purchase_info | AUTO: Pre‑Purchase Question — Intake | |
| t_influencer_inquiry_route | AUTO: Influencer Inquiry — Route | |

Tier 0 acknowledgements are not recommended in early rollout; macros for those can exist but should be used only by humans.

---

## Macro cleanup recommendations (from the current snapshot)
In the exported macro set, watch out for:
- “INSERT ADDRESS” / “XXXX” placeholders (must be removed)
- long paragraphs that are hard for live chat
- macros that disclose address or other sensitive fields by default

Suggested approach:
1) Create the `AUTO:` set first (safe + consistent).
2) Optionally refactor older macros in a later pass:
   - keep agent-only internal macros as-is
   - align customer-facing ones to match the `AUTO:` set

---

## Drift prevention process (operational SOP)
Monthly (or after any macro edit sprint):
1) Export macros from Richpanel to CSV.
2) Diff against `templates_v1.yaml` (copy + placeholders).
3) If drift is detected:
   - decide whether Richpanel or repo is correct
   - update the repo templates and re-sync macros
4) Record changes in:
   - `docs/00_Project_Admin/Change_Log.md`
   - `docs/00_Project_Admin/Decision_Log.md` if policy/customer copy changed

---

## Open questions
- Do you want automation messages to appear as a dedicated “Automation Bot” user in Richpanel, or as the assigned agent/team?  
  (Recommended: a bot identity if Richpanel supports it, for transparency + auditing.)

---

## Wave 08 addendum: agent feedback macros (recommended)

Last updated: 2025-12-22

Wave 05 defines **AUTO:** macros for sending approved reply templates.

Wave 08 adds a separate (optional but strongly recommended) set of **feedback macros** that agents can use to:
- mark a ticket as misrouted
- mark an auto-reply as wrong/helpful
- indicate the correct destination team/queue

Why we include this here:
- it keeps the “macro ecosystem” complete in one place
- it accelerates quality improvements without heavy labeling

Source of truth for feedback macro names + tags:
- `docs/08_Observability_Analytics/Feedback_Signals_and_Agent_Override_Macros.md`

### Naming convention (recommended)
- Feedback macros should be prefixed with: **`MW Feedback:`**
- Feedback tags should be prefixed with: **`mw_feedback_`**

Examples:
- Macro: `MW Feedback: Misrouted → Returns Admin`  
  Tag(s): `mw_feedback_misroute`, `mw_feedback_correct_dept_returns_admin`

- Macro: `MW Feedback: Auto reply wrong`  
  Tag(s): `mw_feedback_auto_reply_wrong`

### Governance rule
Feedback macros **must not** change customer-facing replies.  
They only apply tags/signals for analytics + continuous improvement.

(Template/macros that *send* messages remain in the **AUTO:** macro set.)

