# Multi-intent priority matrix (v1)

Last updated: 2025-12-22  
Scope: Wave 04 (LLM routing design)

## Purpose
Customers often ask multiple things in one message (example: “Where is my order and I want a refund.”).  
We need deterministic rules to decide:

- **primary_intent** (exactly 1)
- **secondary_intents** (0–2)
- **routing destination**
- whether **any automation** is allowed

This matrix prevents:
- unsafe auto-replies when escalation signals are present
- misrouting caused by “easy” intents (like order status) overriding “hard” intents (like chargebacks)
- inconsistent behavior across channels and over time

---

## Core rule
### Tier 0 overrides everything
If any Tier 0 escalation intent is present, it becomes the **primary_intent** and automation is **disabled** (or neutral ACK only).

Tier 0 intents:
- `chargeback_dispute`
- `legal_threat`
- `fraud_suspected`
- `harassment_threats`

---

## Priority levels
Use these priority levels when choosing the primary intent.

### P0 — Escalation (Tier 0)
- chargeback/dispute, legal threats, fraud, harassment

### P1 — Transaction-critical changes
- cancel_order
- address_change_order_edit
- cancel_subscription
- billing_issue *(intake only; still important)*

### P2 — Shipping exceptions & fulfillment claims
- delivered_not_received
- missing_items_in_shipment
- wrong_item_received
- damaged_item

### P3 — Returns / refund outcomes
- return_request
- refund_request
- exchange_request  
*(These are often “desired outcomes” that follow P2 root causes. Route to Returns Admin either way.)*

### P4 — Status / informational
- order_status_tracking
- shipping_delay_not_shipped

### P5 — Product/technical + channel requests
- technical_support
- phone_support_request
- tiktok_support_request
- social_media_support_request

### P6 — Sales / pre-purchase / marketing
- promo_discount_issue
- pre_purchase_question
- influencer_marketing_inquiry

### P7 — Unknown
- unknown_other

---

## Choosing the primary intent (algorithm)
1) Collect candidate intents with their confidences (LLM output).  
2) Apply **Tier 0 override**:
   - if any Tier 0 intent exists → pick the highest confidence Tier 0 intent  
3) Otherwise, pick the intent with the **highest priority level** (P1 beats P2, etc).  
4) If multiple intents share the same priority:
   - prefer the **more specific root-cause workflow** over generic outcomes  
   - otherwise pick the higher-confidence one
5) Secondary intents:
   - include up to 2 remaining intents, sorted by priority (highest first)

---

## Automation rules for multi-intent messages
### Automation is allowed only when:
- primary intent is eligible for Tier 1/2 automation **and**
- there is **no** secondary intent at a higher priority that would require human handling

Practical v1 rule:
- If any P0/P1/P2 intent exists anywhere → **do not send Tier 2 auto-replies**, even if order_status_tracking also appears.
- Tier 1 safe-assist templates are allowed when they are **intake-style** (ask-for-details) and do not disclose sensitive info.

Examples:
- “Where is my order? Also I want to cancel.”
  - primary_intent: cancel_order (P1)
  - secondary: order_status_tracking (P4)
  - automation: Tier 1 cancel intake template (no auto-cancel)
- “My order says delivered but I didn’t get it.”
  - primary_intent: delivered_not_received (P2)
  - automation: Tier 1 DNR intake + route to Returns Admin
- “I’m filing a chargeback because I never received my order.”
  - primary_intent: chargeback_dispute (P0)
  - secondary: delivered_not_received (P2)
  - automation: Tier 0 route (neutral acknowledgement optional)

---

## Destination routing tie-breakers (channel-aware)
After primary_intent is selected, apply these routing tie-breakers:

1) **Channel-first**: if the ticket channel is TikTok/Social and the intent is general/unknown → route to that channel team
2) **Specialist beats general**: if technical_support is primary → route to Technical Support Team even if order status is also present
3) Otherwise route per the standard intent→team mapping in:
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`

---

## Implementation notes
- The LLM can output multiple intents. The **policy engine** applies this matrix deterministically.
- The primary intent selected by the model should be treated as a suggestion; final choice follows this matrix.
- Add new examples discovered in production incidents to:
  - the golden set (for future regressions)
  - `Adversarial_and_Edge_Case_Test_Suite.md`

---

## Change control
Any change to the priority matrix requires:
- Decision Log entry
- update to Golden Set labeling guidelines
- baseline refresh (CI gates re-baselined)
