# Tenant Capabilities Clarifications

Last updated: 2025-12-22

This doc exists because a handful of Richpanel behaviors vary by plan / workspace configuration.

Instead of blocking the plan on uncertain UI details, we:
1) explain *what the question means* in plain English
2) state the **best-suggested default** that works in most tenants
3) list a quick verification task + a fallback so we don’t get stuck


## Important note (who this is for)
If you (project owner) don’t know the answers to the “tenant capability” questions, that’s expected.

These checks are **not** meant to be answered from memory. They are meant to be confirmed by:
- a Cursor agent clicking around the Richpanel admin UI, and/or
- a quick API call using your Richpanel API key.

The plan is designed so we can still proceed using **safe defaults** even if a capability is missing.


---

## 1) “Can we reorder automation rules?”
**What we mean:**
- Richpanel evaluates automation rules in a specific order (usually top-to-bottom inside each automation category).
- If a rule has “**Skip all subsequent rules** = ON”, later rules in the same list might never run.

**Why it matters:**
- If our “Middleware — Inbound Trigger” rule runs **after** a “skip subsequent rules” rule, middleware might never receive events.

**Best-suggested default:**
- Place the middleware trigger as a **Tagging Rule** (or equivalent category) and move it to the **top of that category**.
- Keep “Skip all subsequent rules” **OFF** for the middleware trigger.

**Fallbacks:**
- If HTTP Target action is only available in Assignment Rules, make the middleware trigger the **first Assignment Rule** (skip OFF).
- Worst case: add the trigger action to multiple channel rules and rely on middleware idempotency.

---

## 2) “Can we do a condition like ‘Tags does not contain X’?”
**What we mean:**
- In Richpanel rule conditions, can we check whether a tag is present / absent?

**Why it matters:**
- We need to prevent *routing fights*. Example:
  - Middleware already decided routing and added `mw-routing-applied`.
  - A legacy rule fires on a later message and reassigns the ticket again.

**Best-suggested default:**
- Add a guard condition on legacy assignment rules:
  - `Tags does not contain mw-routing-applied`
- Also turn off “Reassign even if already assigned” where possible.

**Fallbacks:**
- If “tag not present” conditions aren’t supported, turning off “reassign even if already assigned” usually prevents overrides.

---

## 3) “What variables are available in HTTP Target payload templates?”
**What we mean:**
- When defining the HTTP Target body, what placeholders can we reference?
  - Example: `{{ticket.id}}`, `{{ticket.url}}`, `{{ticket.lastMessage.text}}`

**Why it matters:**
- This decides whether we can send only `ticket_id`, or also include the latest customer message in the webhook payload.

**Best-suggested default:**
- Start with a minimal JSON payload:
  - `ticket_id`, `ticket_url`, `trigger`
- Only add `ticket.lastMessage.text` after verifying Richpanel **escapes JSON safely** (test with quotes/newlines).

---

## 4) “Do we actually have order status / tracking from Richpanel + Shopify integration?”
**What we mean:**
- When a customer messages in Richpanel, is their Shopify order linked such that Richpanel APIs return:
  - order id, app client id
  - order details including fulfillment tracking number/URL

**Why it matters:**
- We only want to auto-answer order status when we can be correct.

**Best-suggested default:**
- Use Richpanel order linkage API as a deterministic gate:
  - if no order is linked, do **not** auto-share tracking details
- Only auto-reply on order status when deterministic match exists.

**Fallbacks:**
- Ask customer for order number.
- If later we gain Shopify Admin API access, use it as a fallback lookup (Wave 05+).

---

## Quick “tenant verification” checklist (Wave 03)
Cursor agents should confirm:
- [ ] middleware trigger can exist as a Tagging Rule and call HTTP Target
- [ ] custom headers supported (`X-Middleware-Token`)
- [ ] JSON escaping for `{{ticket.lastMessage.text}}` (optional)
- [ ] `GET /v1/order/{conversationId}` returns linked order vs `{}` consistently in your tenant
