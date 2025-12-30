# No-Tracking Delivery Estimate Automation (Order Status)

Last updated: 2025-12-29  
Status: **Draft (CR-001)**

## Purpose
When customers ask for order status **before a tracking number exists**, we send a conservative delivery estimate derived from:
- the order’s shipping bucket (Standard / Rushed / Priority / Pre-Order), and
- business days elapsed since order placement.

This is designed to reduce order-status ticket volume while remaining safe:
- deterministic order match required
- templates only (no free-form model replies)
- explicit auto-close allowlist (reply-to-reopen)

See: `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md`

---

## When this automation applies

### Preconditions (must be true)
1) Customer message intent is one of:
   - `order_status_tracking`
   - `shipping_delay_not_shipped`
2) Deterministic match to a **single** order exists.
3) Order has **no tracking number** (and no tracking URL) available.

### Exclusions (fail closed)
- Multiple matching orders
- Shipping bucket cannot be determined from verified order data
- Pre-order estimate is missing for a pre-order order
- Any Tier 0 escalation flags present
- Confidence gates fail (see below)

---

## Inputs required
From verified order data (Richpanel or Shopify fallback):
- `order_id`
- `order_created_at` (timestamp)
- `shipping_method_name` (raw string)
- `tracking_number` and `tracking_url` (must be missing to use this flow)

For pre-orders (one of):
- `preorder_eta_business_days`, OR
- `preorder_ship_by_date`, OR
- a tag/metafield value we can deterministically parse

From the ticket:
- `ticket_created_at`

---

## Shipping bucket mapping

### Buckets (v1)
| Bucket | SLA window (business days) |
|---|---|
| Standard | 3–5 |
| Rushed | 1 |
| Priority | 1 |
| Pre-Order | varies |

### Mapping rule (v1)
Normalize `shipping_method_name` -> `shipping_bucket` using a small mapping table.

If no mapping match:
- do not estimate
- fall back to Tier 1 intake or route-only

---

## Business day calculation (v1)

### Definition
Business days are **Monday–Friday**.
Holiday calendars are not required for v1 (open question).

### Elapsed business days
We compute:
- `elapsed_bd = business_days_between(order_created_at, ticket_created_at)`

Rule of thumb:
- order placed Monday, ticket Wednesday -> `elapsed_bd = 2`

### Remaining window
For window `[min_bd, max_bd]`:
- `remaining_min = max(0, min_bd - elapsed_bd)`
- `remaining_max = max(0, max_bd - elapsed_bd)`

### Format string
Middleware produces a single string:
- if `remaining_min == remaining_max`: `<N> business days`
- else: `<A>–<B> business days`

This is passed into the template as:
- `eta_remaining_human`

---

## Late / out-of-window handling
If `elapsed_bd >= max_bd` (i.e., `remaining_max == 0`), then the order is outside its SLA window:
- do not auto-close
- send an escalation-safe template and route to a human

> Note: We are not promising compensation or refunds. We are only escalating.

---

## Confidence and safety gates

### Tier 2 eligibility (existing)
Must satisfy Tier 2 thresholds from:
- `docs/04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

### Auto-close eligibility (new)
Auto-close may occur only if:
- template_id is whitelisted for auto-close
- order is within SLA window (`remaining_max > 0`)
- the response includes reply-to-reopen language

---

## Template(s)

### Tier 2 estimate (new)
- `t_order_eta_no_tracking_verified`

Required variables:
- `order_id`
- `shipping_bucket`
- `eta_remaining_human`

Optional variables:
- `first_name`
- `order_created_date_human`

---

## Examples

### Example A — Standard
- Order: Monday morning, Standard (3–5 business days)
- Ticket: Wednesday morning, no tracking
- Computation:
  - elapsed_bd = 2
  - remaining = 1–3 business days
- Output:
  - send `t_order_eta_no_tracking_verified`
  - auto-close (eligible)

### Example B — Pre-Order
- Order: 2025-11-03
- Pre-order ETA: 45 business days
- Ticket: 2025-11-24, no tracking
- Computation:
  - remaining = 29 business days
- Output:
  - send `t_order_eta_no_tracking_verified`
  - auto-close (eligible)

---

## Logging and audit expectations
For every auto-sent estimate, log an internal “audit block”:
- order_id
- raw shipping_method_name
- normalized shipping_bucket
- order_created_at
- ticket_created_at
- elapsed_bd
- remaining_min / remaining_max
- eta_remaining_human
- template_id
- whether ticket was auto-closed

---

## Open questions
1) Holiday calendar: do we need to exclude US holidays?
2) Exact shipping method strings in Shopify/Richpanel for each bucket.
3) Pre-order source-of-truth for ETA (field, tag, product table).
4) Richpanel semantics for “Resolved” and reopen-on-reply.
