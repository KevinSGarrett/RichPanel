# Top FAQs Playbooks (v1)

Last updated: 2025-12-29  
Status: **Final (Wave 05 closeout)**

## Purpose
For each high-volume FAQ intent, define:
- what triggers it (typical customer language)
- required entities/data
- which **template_id** (if any) is allowed in early rollout
- routing destination (team + tags)
- key edge cases and “fail closed” rules

These playbooks are designed to be used by:
- the LLM prompt design (intent definitions)
- the policy engine (what is allowed)
- the implementation team (middleware + Richpanel rule coordination)
- QA (what to test)

## Priority order (by volume)
From RoughDraft analysis (3,611 tickets):
1) **Order status & tracking** (~52%)
2) Cancel order (~6.7%)
3) Product/app troubleshooting (~4.8%)
4) Cancel subscription (~3.9%)
5) Missing items (~3.5%)
6) Shipping delay / not shipped (~3.2%)
7) Diffuser not misting (~2.6%)
8) App connectivity/setup (~2.5%)
9) Return/exchange/refund (~2.4%)
10) Pre-order/backorder status (~2.2%)

Also important operational bucket:
- **Chargeback/dispute** (~87 tickets)

---

## 1) Order status & tracking (`order_status_tracking`)
**Examples of customer phrasing**
- “Where is my order?”
- “Tracking says delivered / still in transit”
- “What’s my tracking number?”
- “Has it shipped yet?”

**Required data**
- Deterministic match to a single order OR ask for order number.

**Allowed automation**
- Tier 2 verified (deterministic match required):
  - `t_order_status_verified` (tracking exists)
  - `t_order_eta_no_tracking_verified` (no tracking yet + within SLA window)
  - `t_shipping_delay_verified` (no tracking yet + outside SLA window)
- Tier 1 fallback:
  - `t_order_status_ask_order_number`
**Routing**
- Primary: **Email Support Team**
- Channel-first exception: if channel is live chat/messenger → LiveChat Support team may already be assigned by Richpanel rule.  
- Tags to add:
  - `mw-intent-order-status`
  - `mw-auto-eligible` (only if deterministic match)
  - `mw-auto-sent` (only if we send)

**Auto-close behavior (Tier 2 estimate only)**
- If we send `t_order_eta_no_tracking_verified` and Tier 2 gates pass: mark ticket **Resolved** and add tag `mw:auto_closed`.
- The message must include “reply to reopen” language.

**Fail-closed rules**
- No linked order → never disclose tracking; ask for order number.
- Multiple linked orders/ambiguous → ask for order number.
- Any Tier 0 risk keywords present → escalate (no auto-reply).

See full spec: `Order_Status_Automation.md`.

---

## 2) Shipping delay / not shipped (`shipping_delay_not_shipped`)
**Examples**
- “It’s been a week and it hasn’t shipped”
- “Still processing”
- “When will it ship?”

**Allowed automation**
- Tier 2 verified (linked order):
  - `t_order_eta_no_tracking_verified` (if within SLA window)
  - `t_shipping_delay_verified` (if outside SLA window)
- Tier 1 fallback: `t_order_status_ask_order_number`
**Routing**
- Email Support Team (or channel-first if live chat)
- Tag `mw-intent-shipping-delay`

**Fail-closed**
- Do not promise an exact delivery date/time.
- Only provide a remaining **business-day window** via the approved ETA template.
- Never promise compensation.

---

## 3) Cancel order (`cancel_order`)
**Examples**
- “Cancel my order”
- “I ordered the wrong item, please cancel”

**Allowed automation**
- Tier 1 intake only: `t_cancel_order_ack_intake`  
  (No auto-cancel; Tier 3 disabled.)

**Routing**
- Email Support Team
- Tag `mw-intent-cancel-order`

**Key edge cases**
- If customer indicates a dispute/chargeback is filed → route to Chargebacks/Disputes Team (Tier 0).
- If customer asks to “cancel subscription” vs “cancel order”: separate intent.

---

## 4) Cancel subscription (`cancel_subscription`)
**Examples**
- “Cancel my subscription”
- “Stop recurring shipments”

**Allowed automation**
- Tier 1 intake: `t_cancel_subscription_ack_intake`

**Routing**
- Email Support Team (or a Subscription/Billing team if you create one)
- Tag `mw-intent-cancel-subscription`

**Edge cases**
- If customer is demanding a refund for subscription charges → also add `mw-intent-billing` and route appropriately.

---

## 5) Missing items in shipment (`missing_items_in_shipment`)
**Examples**
- “My package arrived but something is missing”
- “Only got part of my order”

**Allowed automation**
- Tier 1 intake: `t_missing_items_intake`
- Always route to human.

**Routing**
- Returns Admin (fulfillment exceptions)
- Tag `mw-intent-missing-items`

**Edge cases**
- Partial fulfillment vs true missing item: still intake first, then human verifies.

---

## 6) Delivered not received (`delivered_not_received`)
**Examples**
- “Tracking says delivered but I don’t have it”
- “Stolen package”

**Allowed automation**
- Tier 1 intake: `t_delivered_not_received_intake`
- Always route to human.

**Routing**
- Returns Admin
- Tag `mw-intent-dnr`

**Fail-closed**
- Do not promise replacements/refunds automatically.

---

## 7) Wrong item received (`wrong_item_received`)
**Allowed automation**
- Tier 1 intake: `t_wrong_item_intake`

**Routing**
- Returns Admin
- Tag `mw-intent-wrong-item`

---

## 8) Damaged item (`damaged_item`)
**Allowed automation**
- Tier 1 intake: `t_damaged_item_intake`

**Routing**
- Returns Admin (or Technical Support if this is a warranty/defect flow; confirm internally)
- Tag `mw-intent-damaged-item`

---

## 9) Product/app troubleshooting (`technical_support`)
This includes:
- diffuser not misting / no mist
- app connectivity / pairing / Wi‑Fi issues
- general “it’s not working”

**Allowed automation**
- Tier 1 intake: `t_technical_support_intake`
- Always route to human.

**Routing**
- Preferred: Technical Support Team  
- If that team does not exist in Richpanel yet:
  - route to Email Support Team + tag `mw-needs-tech-support`

**Edge cases**
- If customer is threatening chargeback/refund: also classify `billing_issue` and route accordingly.

---

## 10) Return / exchange / refund (`return_request`, `exchange_request`, `refund_request`)
**Allowed automation**
- Tier 1 intake:
  - `t_return_request_intake`
  - `t_exchange_request_intake`
  - `t_refund_request_intake`

**Routing**
- Returns Admin
- Tags: `mw-intent-return`, `mw-intent-exchange`, `mw-intent-refund`

**Fail-closed**
- Do not approve returns/refunds automatically in v1.

---

## 11) Promo/discount issues (`promo_discount_issue`)
**Allowed automation**
- Tier 1 info: `t_promo_discount_info`

**Routing**
- Sales Team preferred  
- If Sales is not staffed in Richpanel: Email Support Team + tag `mw-needs-sales`

---

## 12) Pre-order / backorder status (`preorder_backorder_status`)
**Allowed automation**
- If linked order exists:
  - often handled via `t_shipping_delay_verified`
- Else:
  - `t_order_status_ask_order_number`

**Routing**
- Email Support Team
- Tag `mw-intent-preorder`

---

## Chargebacks / disputes (`chargeback_dispute`) — Tier 0
**Allowed automation**
- Recommendation: **route only** (no auto-reply in v1)  
- If you choose to acknowledge, use `t_chargeback_neutral_ack` and keep it neutral.

**Routing**
- Chargebacks / Disputes Team  
- If not created: Leadership Team + tag `mw-needs-chargebacks-queue`

---

## Implementation note: policy + playbooks must agree
Any time we:
- add a new intent
- change routing for an intent
- enable/disable a template

Then we must update:
- `Department_Routing_Spec.md`
- `Decision_Pipeline_and_Gating.md`
- `Template_ID_Catalog.md` / `Templates_Library_v1.md`
- regression tests / eval datasets
