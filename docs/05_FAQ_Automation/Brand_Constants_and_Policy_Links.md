# Brand Constants and Policy Links

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Keep **brand-specific** values (name, signature, help/policy links) out of individual templates so:
- templates stay reusable and versioned
- copy stays consistent across channels
- updates (policy URL changes, signature changes) happen in one place

Machine-readable file:
- `templates/brand_constants_v1.yaml`

---

## V1 default posture (selected to close Wave 05)
- **Signature:** enabled via `{{support_signature}}` (defaults to **Customer Support**).
- **Policy links:** **disabled by default** (all URLs empty) to avoid shipping incorrect links.  
  Links can be enabled later by populating the YAML file.

This lets implementation proceed safely even if brand URLs are not finalized.

---

## Rendering rules (recommended)
### Required global variables (v1)
These should always be provided to templates:
- `support_signature`

`brand_name` is optional in v1 (kept for future enhancement) and may remain unset.

If missing, middleware should fall back to safe defaults:
- `support_signature = "Customer Support"`

### Optional global variables
These may be included only if set:
- `help_center_url`
- `returns_policy_url`
- `shipping_policy_url`
- `privacy_policy_url`
- `warranty_policy_url`
- `order_status_portal_url`

---

## Pre-production checklist (must-do before go-live)
Before production rollout, confirm:
1) `support_signature` is set to your preferred brand signature
2) any URLs included are correct and public
3) templates that include links remain accurate in both LiveChat and Email formatting

See: `docs/05_FAQ_Automation/Pre_Launch_Copy_and_Link_Checklist.md`
