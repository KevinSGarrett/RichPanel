# CR-001 — No-Tracking Delivery Estimate Automation (Order Status)

Last updated: 2025-12-29  
Status: **Draft (scoped for implementation in Build Mode)**

## Problem statement
Tracking numbers are not created/sent to customers until a package is boxed and shipped.
This creates a high volume of “order status” tickets from customers who cannot see tracking yet.

We cannot change shipping operations or tracking issuance timing, so we need a safe automation strategy to:
- answer common order-status questions when tracking does **not** exist yet, and
- deflect/close tickets when we can answer with high confidence.

## Goals
1) Reduce order-status ticket volume caused by “no tracking yet”.
2) Provide **accurate, conservative** delivery estimates using only verified order data.
3) Auto-close tickets **only** when the answer is high-confidence and low-risk, while preserving a path to a human (reply-to-reopen).
4) Keep everything deterministic and auditable (no free-form LLM replies).

## Non-goals
- Changing fulfillment operations or when tracking numbers are created.
- Promising an exact delivery date/time.
- Offering compensation, credits, refunds, or policy exceptions via automation.

## User-facing behavior
When a customer asks for order status and **no tracking exists yet**, the middleware will:

1) Verify we have a deterministic match to a single order.
2) Identify the shipping “bucket” from the order’s shipping method.
3) Compute the remaining delivery window in **business days** (relative to the order date).
4) Send an automated template response with the remaining window.
5) Auto-close the ticket if eligible (see **Auto-close rules** below).

If we cannot compute the window with high confidence, we fail closed:
- send a safe Tier 1 intake (“please provide order #”), or
- route to a human without sending a customer-specific estimate.

## Shipping buckets and SLAs (v1 defaults)
These are the initial SLA windows used for *order-to-delivery* estimates.

| Bucket | SLA (business days) | Notes |
|---|---:|---|
| Standard | 3–5 | “3–5 business days shipping” |
| Rushed | 1 | “24 business hours” (treated as 1 business day) |
| Priority | 1 | “24 business hours” (treated as 1 business day) |
| Pre-Order | varies | Derived from preorder estimate (see below) |

### Pre-Order SLA source (v1)
Pre-order timing must be derived from verified order data, using one of:
- an explicit `preorder_eta_business_days` field (preferred), or
- a tag/metafield that encodes expected ship/arrival date, or
- a product-level preorder policy table.

If none are available: **do not estimate** (route to human).

## Calculation rules (v1)
**Business day definition:** Monday–Friday.  
Holiday calendar support is optional (see open questions).

Let:
- `order_created_at` = verified order create timestamp (store timezone)
- `ticket_created_at` = inbound ticket timestamp (store timezone)
- `elapsed_bd` = business days elapsed between `order_created_at` date and `ticket_created_at` date

For a bucket with SLA window `[min_bd, max_bd]`:
- `remaining_min = max(0, min_bd - elapsed_bd)`
- `remaining_max = max(0, max_bd - elapsed_bd)`

### Human formatting
The middleware formats a customer-facing window:
- If `remaining_min == remaining_max`: “<N> business days”
- Else: “<A>–<B> business days”

### Late / out-of-window handling
If `elapsed_bd >= max_bd` (i.e., `remaining_max == 0`):
- **Do not auto-close.**
- Send an escalation-safe message (no promises), and route to a human.

## Confidence gating (v1)
This automation uses Tier 2 verified templates and must satisfy **all** Tier 2 gates:
- intent in allowed set: `order_status_tracking`, `shipping_delay_not_shipped`
- `routing_confidence >= 0.70`
- deterministic match to a single order
- Tier 2 verifier approves (`verified == true` and `tier2_verifier_confidence >= 0.80`)
- no Tier 0 flags present

If any gate fails: fall back to Tier 1 intake or route-only.

## Auto-close rules (v1)
Auto-close is allowed **only** when:
1) The selected `template_id` is explicitly marked **auto-close allowed** (whitelist).
2) The order is **within** its SLA window (`remaining_max > 0`).
3) Tier 2 confidence gating passes (above).
4) The reply template includes a **reply-to-reopen** sentence.

Auto-close action:
- mark conversation as **Resolved** (not “hard closed”)
- apply tags: `mw:auto_closed`, `mw:deflected`, and intent tags
- add an internal note containing the computed window and inputs (for audit)

## Templates and IDs
New template(s) introduced by this change request:
- `t_order_eta_no_tracking_verified` (Tier 2, auto-close eligible)

See:
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- `docs/05_FAQ_Automation/Templates_Library_v1.md`
- `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`

## Acceptance criteria (examples)
### Example A — Standard
- Order placed: Monday (Standard 3–5 business days)
- Ticket submitted: Wednesday
- Tracking: missing
- Expected response: “arrive in **1–3 business days**”
- Ticket auto-closed (eligible).

### Example B — Pre-Order
- Preorder placed: 2025-11-03
- Preorder SLA: 45 business days
- Ticket submitted: 2025-11-24
- Tracking: missing
- Expected response: “arrive in **29 business days**”
- Ticket auto-closed (eligible).


## Wave plan (pre-build)
- **Wave F13:** Add CR-001 spec + templates + routing/policy updates to the foundation docs (this repo update).
- **Wave F14:** Finalize CR-001 open questions (shipping method mapping, preorder ETA source, holiday calendar) and lock final copy + thresholds.

## Implementation checklist (Build Mode)
- [ ] Define shipping method normalization -> bucket mapping table
- [ ] Define preorder SLA source precedence (field -> tag/metafield -> policy table)
- [ ] Implement business-day calculator (Mon–Fri v1; optional holiday list)
- [ ] Implement ETA window compute + formatter (`eta_remaining_human`)
- [ ] Add `t_order_eta_no_tracking_verified` to templates YAML + library + Template ID catalog
- [ ] Update gating logic: allow auto-close only for whitelisted template IDs
- [ ] Implement Richpanel conversation “resolve” action + confirm reply reopens
- [ ] Add unit tests for business-day math (including weekends)
- [ ] Add integration tests: no-tracking estimate path, late/out-of-window path
- [ ] Add eval cases in offline dataset + regression suite
- [ ] Add metrics: deflection rate, reopen rate, late-escalation rate
- [ ] Add kill-switch coverage: automation disabled -> always route

## Open questions (to resolve before production)
1) Holiday calendar: do we need to exclude US holidays or treat business days as Mon–Fri only?
2) Shipping method strings: what are the exact values returned by Shopify/Richpanel that map to Standard/Rushed/Priority/Pre-Order?
3) Pre-order data source: where will `preorder_eta_business_days` (or equivalent) come from?
4) Auto-close semantics in Richpanel: confirm “Resolved” + customer reply reopens automatically.
