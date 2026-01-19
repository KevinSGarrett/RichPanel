# Order Status Automation (v1)

Last updated: 2025-12-29  
Status: **Updated (CR-001 scoped)**

Note: Richpanel tenant verification tasks are deferred, but this design remains safe because it fails closed:
- Tier 2 replies require deterministic order match
- otherwise we send Tier 1 intake + route to a human


## Goal
Automatically respond to “Where is my order?” / “tracking?” questions **only when safe**, using Tier 2 verified templates.

This is our highest-volume FAQ (~52% of tickets from RoughDraft analysis).  
Done correctly, it can deflect a large amount of repetitive work without creating customer harm.

## Non-negotiable safety constraints
These are **hard rules** (fail closed):

1) **Deterministic match is required** before disclosing:
   - tracking number
   - tracking link
   - order status link
   - any order-specific facts (delivered/shipped, etc.)

2) If we cannot confidently match exactly one order to the requesting customer:
   - do **not** guess
   - do **not** disclose
   - send `t_order_status_ask_order_number` and route to a human

3) Do **not** include shipping/billing addresses in automated replies (even if available).
   - This avoids accidental disclosure and reduces perceived “creepiness”.

4) Auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) tickets.

5) **Order context required** before any order-status auto-reply:
   - order_id (stable identifier) + order created_at
   - and either tracking signals OR a normalized shipping-method window
   - if missing: suppress auto-reply, route to Email Support Team, tag `mw-order-lookup-failed` + `mw-order-status-suppressed`,
     and log the missing fields for audit/debug.

These constraints align with the common issue: “wrong order → privacy leak” (`CommonIssues/10-order-status-pitfalls.md`).

---

## Definitions

### Deterministic match
A deterministic match is one of the following (in descending preference):

**A) Richpanel linked order**
- The conversation has a linked order returned by Richpanel’s “order linked to conversation” API.
- This is the preferred path because the link is created within your support system and generally implies correct identity association.

**B) Verified customer-provided match (fallback path)**
- Customer provides order number + email/phone (or order number + ZIP, if you later choose).
- Middleware validates that:
  - the order exists, and
  - the order’s email/phone matches the provided identifier.
- Only then can Tier 2 verified templates be used.

> Early rollout recommendation: **only enable path (A)**.  
> Path (B) can be enabled later after you are confident in your validation + rate limiting + monitoring.

---

## Data sources (v1)
Primary:
- Richpanel Order object linked to the conversation (Shopify-integrated orders should populate here if integration is correct).

Secondary (future):
- Shopify Admin API as a fallback (only if Richpanel order linkage is incomplete).
  - This adds complexity and auth surface area; keep out of v1 unless needed.

---

## High-level decision flow (v1)
1) **Classify** message intent  
   - If intent is not `order_status_tracking` or `shipping_delay_not_shipped`: do not enter this flow.

2) **Policy gates**  
   - Tier 0 override? If yes → route to escalation, no auto-reply.
   - Confidence below threshold? → route only (or Tier 1 ask for order number).
   - If qualifies as order-status FAQ: proceed.

3) **Fetch linked order**
   - Call Richpanel: “Retrieve an Order Linked to a Conversation”.
   - If no linked order:
     - send `t_order_status_ask_order_number` (Tier 1)  
     - route to Email Support Team (or your order support queue)
     - tag `mw-order-lookup-needed`

3b) **Order context gate**
   - Require: order_id + created_at + (tracking signal OR normalized shipping-method window).
   - If missing: do not auto-reply or auto-close.
   - Route to Email Support Team and apply: `route-email-support-team`, `mw-order-lookup-failed`, `mw-order-status-suppressed`
     (optionally add a reason tag like `mw-order-lookup-missing:order_id`).

4) **Select response template**
   - If fulfillment/tracking is present → `t_order_status_verified`
   - Else (not shipped yet) → `t_shipping_delay_verified`

5) **Render template with allowed variables only**
   - Allowed fields:
     - order_id
     - status / fulfillment status
     - tracking_company, tracking_number, tracking_url (if present)
     - status_url (if present)
   - Disallowed:
     - full address
     - payment method details
     - full item list (optional in later waves, but avoid in v1)

6) **Send reply**
   - Tag the conversation so we can prevent duplicate auto-replies:
     - `mw-auto-replied`
     - `mw-template-<template_id>`
     - `mw-order-status-auto-v1`

7) **Route to team**
   - Even if we auto-reply, we still route the ticket to the correct team if follow-up is likely.
   - For order status replies, routing can be:
     - route to Email Support Team (default)
     - OR leave unassigned if the goal is pure deflection  
       (recommendation: keep routing on for early rollout so humans can catch failures)

---

## Response selection matrix (v1)

| Order signals (from linked order) | Template | Why |
|---|---|---|
| `tracking_url` exists OR fulfillment has tracking | `t_order_status_verified` | Customer likely wants tracking; we can provide it when linked and verified. |
| No tracking yet + within SLA window (bucket recognized) | `t_order_eta_no_tracking_verified` | We can safely provide a conservative delivery window derived from verified order date + shipping bucket. Eligible for auto-close. |
| No tracking yet + outside SLA window OR bucket unknown | `t_shipping_delay_verified` | Avoid promises. A human should review delays outside the expected window or ambiguous shipping methods. |
| Order missing / ambiguous | `t_order_status_ask_order_number` | Fail closed; request identifiers. |

See also:
- `docs/05_FAQ_Automation/No_Tracking_Delivery_Estimate_Automation.md` (CR-001 spec)
- `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md`

---

## Edge cases and how we handle them (v1)

### Customer has multiple orders
- If Richpanel returns multiple orders (or ambiguous reference): **do not pick one**.
- Send `t_order_status_ask_order_number` and route.

### Partial fulfillment
- If some items are shipped and tracking exists:
  - use `t_order_status_verified`
  - avoid listing items in v1 (keep simple)

### Delivered but customer says “not received”
- Do not send tracking details unless deterministic match exists (linked order).
- Even with a linked order, this is a **fulfillment exception**:
  - Send `t_delivered_not_received_intake` (Tier 1) and route to Returns Admin
  - Optional: include tracking link only if you later confirm this is acceptable (v2)

### Preorder / backorder
- If the order is a pre-order and **no tracking exists yet**:
  - If a verified preorder ETA is available, use `t_order_eta_no_tracking_verified` and auto-close (eligible).
  - If preorder ETA is missing/ambiguous, use `t_shipping_delay_verified` and route to a human.
  - See `docs/05_FAQ_Automation/No_Tracking_Delivery_Estimate_Automation.md`.

- If we auto-close (ETA known and within window): no routing assignment required.
- If we route (ETA missing/late): Email Support Team.

### Customer asks for “change address / cancel”
- These are order-management actions; Tier 3 is disabled.
- Use Tier 1 intake templates:
  - `t_cancel_order_ack_intake`
  - `t_address_change_ack_intake`
- Route to your order-management handler (Email Support Team or a dedicated team if created).

---

## De-duplication (automation loop prevention)
Minimum required checks before sending an order-status auto-reply:

- If ticket already has tag `mw-auto-replied` within last X minutes → do not auto-reply again.
- If the last message was from an agent (not the customer) → do not auto-reply.
- If the ticket is closed/solved → do not auto-reply.
- If a prior auto-reply was sent for this same inbound message id → do not auto-reply.

When a ticket is skipped, the worker routes to Email Support and applies tags for visibility:
- Closed/solved: `route-email-support-team`, `mw-escalated-human`, `mw-auto-skipped-resolved`
- Follow-up after middleware auto-reply: `route-email-support-team`, `mw-escalated-human`, `mw-auto-skipped-followup`
- Ticket status read failed: `route-email-support-team`, `mw-escalated-human`, `mw-auto-skipped-status-read-failed`

See: `FAQ_Automation_Dedup_Rate_Limits.md` and common issue `01-automation-loops.md`.

---

## Monitoring and QA (v1)
Track these metrics daily:
- Auto-replies sent (count) by template_id
- Auto-reply success vs fallback (`mw-order-lookup-needed`)
- Customer follow-up rate within 24h (“that’s wrong”, “still not here”)
- Human override rate (agent changed routing or tags)
- Error rate on order lookup APIs

Alerting:
- Spike in `mw-order-lookup-needed`
- Spike in “wrong order” complaints (manual tag by agents)

---

## Open questions (tracked)
- Do we have a customer-facing order status portal link we prefer (Richpanel statusUrl vs Shopify order status page)?
- What are your actual processing/shipping SLAs (so we can avoid inventing timeframes)?
- Should we include tracking **number** or only tracking **link** in the automated reply (v1 includes both if available)?