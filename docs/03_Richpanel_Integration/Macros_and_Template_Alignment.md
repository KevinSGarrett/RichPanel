# Macros and Template Alignment (Richpanel ↔ Middleware)

Last updated: 2025-12-21
Last verified: 2025-12-21 — Added v1 mapping from key middleware auto-replies to existing Richpanel macros (tone + content baseline).

Goal: When middleware sends automated replies, they should:
- match your existing **brand voice** and support style
- reuse the *content intent* of Richpanel macros where appropriate
- avoid risky disclosures (PII) unless deterministic identity match is confirmed

> Important: Middleware cannot reliably “apply a Richpanel macro” via API (macros are an agent UI feature).
> Instead, we treat macros as the **content source of truth** and mirror equivalent templates in middleware config.

---

## 1) Template design rules (v1)
1) **No promises**: avoid “we have refunded” unless confirmed by system action.
2) **Deterministic match gating** for sensitive order info:
   - tracking link/number, order status → only when deterministic match exists
3) **No full-address disclosure** in automated replies (even if macro includes it). City/state is okay if deterministic match.
4) **Keep it short**: Tier 1 and Tier 2 replies should be 3–8 lines, with a clear next step.
5) **Always provide a human path**: “If this doesn’t look right, reply with …”

---

## 2) Known relevant macros in your current Richpanel setup (snapshot 2025-12-19)

Below are high-value macros we should align with for v1.

### 2.1 Order status / tracking (FAQ automation Tier 2 when deterministic match)
- **Macro:** `ORDERS: Tracking Request`  
  - Snapshot ID: `rp.current-setup.macro.orders-tracking-request` (Macro row 112)
  - Use for: “Where is my order?” / “Tracking?” / “Has it shipped?”
  - Middleware adaptation:
    - include: order number, fulfillment status, tracking link
    - omit: any address lines

### 2.2 Delivered-but-not-received (DNR) (Tier 1 safe-assist + route to Returns Admin)
- **Macro:** `ORDERS: Package Delivered`  
  - Snapshot ID: `rp.current-setup.macro.orders-package-delivered` (Macro row 23)
  - Use for: “Tracking says delivered but I don’t have it”
  - Middleware adaptation:
    - safe-assist checklist (neighbors/mailroom/24h wait)
    - if deterministic match: include tracking link; **do not** include full address
    - always route to human (Returns Admin / Claims)

### 2.3 Tracking not updating / stalled (Tier 1 assist + route)
- **Macro:** `ORDERS: Contact Warehouse/Tracking Not Updated`  
  - Snapshot ID: `rp.current-setup.macro.orders-contact-warehouse-tracking-not-updated` (Macro row 48)
  - Use for: “Tracking hasn’t updated” / “Stuck in pre-shipment”
  - Middleware adaptation:
    - explain typical carrier scan delays
    - provide tracking link when deterministic match exists
    - route to Returns Admin if beyond threshold

### 2.4 Tracking updated / in transit (Tier 2 when deterministic match)
- **Macro:** `ORDERS: Tracking Updated to Show In Transit`  
  - Snapshot ID: `rp.current-setup.macro.orders-tracking-updated-to-show-in-transit` (Macro row 95)

### 2.5 Chargebacks/disputes (Tier 0 human-only; used by agents)
- **Dispute/chargeback macros** exist (examples in snapshot):
  - `DISPUTES: Chargeback Lost`
  - `DISPUTES: Chargeback In Progress`
  - `Manager Only Outreach Chargeback Order Shipped`
- **Middleware rule (v1):** never auto-send dispute/chargeback templates to customers.

---

## 3) What we will template in middleware (v1)
### 3.1 Tier 2 (verified auto-reply)
- Order status + tracking (deterministic match only)

### 3.2 Tier 1 (safe-assist, no sensitive disclosure)
- Delivered-but-not-received acknowledgement + checklist
- Missing/incorrect/damaged intake request (ask for order #, photos, items)

### 3.3 Tier 0 (no automation)
- Chargebacks/disputes
- Legal threats / “lawsuit”
- Fraud reports
- Payment processor notifications (route only)

---

## 4) Template governance (to avoid drift)
- Store middleware templates in a versioned config file (YAML/JSON) with:
  - template_id
  - tier
  - allowed_disclosures (tracking_link, order_status, address_city_state, etc.)
  - required_inputs (order_id, tracking_url, etc.)
- Support Ops owns content approval.
- Engineering owns safe gating + redaction.

