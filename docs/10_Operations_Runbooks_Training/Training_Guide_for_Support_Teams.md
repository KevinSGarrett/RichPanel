# Training guide for support teams

Last updated: 2025-12-22

This guide is for Support agents, Support Ops, and team leads using Richpanel alongside the middleware.

Goal: ensure humans and automation collaborate safely.

---

## What the middleware does (in plain English)
- Reads inbound customer messages.
- Assigns a **routing intent** and applies **routing tags** / team routing.
- For a small set of FAQs, it may send an **automated reply** using approved templates.
- For high-risk topics (Tier 0), it always routes to humans and avoids automation.

It does **not**:
- close tickets automatically
- process refunds/cancellations automatically (v1)
- replace agents; it reduces repetitive work and improves routing

---

## What you will see in Richpanel

### Routing tags (examples)
- `mw:intent:order_status_tracking`
- `mw:intent:returns_refund_request`
- `mw:intent:shipping_missing_items`
- `mw:tier:1` / `mw:tier:2` / `mw:tier:0`
- `mw:routed:true`
- `mw:automation_sent:true` (only when an auto-reply was actually sent)

### How to interpret confidence
Agents should treat confidence as:
- a **hint**, not a guarantee
- if the customer’s message contradicts the assigned team, override and tag feedback

### Automation messages
If an auto-reply is sent:
- it uses pre-approved templates (Wave 05)
- it should never include sensitive information unless deterministic match exists (Tier 2)

---

## How to override routing (agent actions)
When you believe routing is wrong:
1. Reassign the ticket to the correct team (normal Richpanel action).
2. Apply the feedback tag:
   - `mw:feedback:misroute`
3. Optionally apply a more specific tag:
   - `mw:feedback:wrong_intent:<intent_name>`
4. Add a short internal note with the reason (“customer asking about returns, not order status”).

This feedback is used for weekly calibration (Wave 08).

See:
- [Richpanel agent override and feedback](training/Richpanel_Agent_Override_and_Feedback.md)

---

## Key workflows (v1)

### Chargebacks / disputes
- Always human-handled (Tier 0).
- Routed to **Chargebacks / Disputes** team.
- Automation is disabled except optional neutral acknowledgement.

Runbook:
- [R008 — Chargebacks / disputes process](runbooks/R008_Chargebacks_Disputes_Process.md)

### Shipping exceptions (missing/wrong/damaged/DNR)
- Routed to Returns Admin (v1 simplicity).
- May send a Tier 1 “intake” message asking for missing details (order #, photos, etc.).

Runbook:
- [R009 — Shipping exceptions / returns workflow](runbooks/R009_Shipping_Exceptions_Returns_Workflow.md)

### Order status / tracking
- Tier 2 only (deterministic match required).
- If no deterministic match, the system requests order # and routes.

Reference:
- [Order status automation](../05_FAQ_Automation/Order_Status_Automation.md)

---

## When to escalate (Support Ops / leadership)
Escalate immediately if:
- customers report wrong personal details (possible PII leak)
- repeated wrong replies across multiple tickets
- chargeback/dispute messages are being mishandled
- automation “loops” (repeated messages) are observed

Use:
- [On-call and escalation](On_Call_and_Escalation.md)

---

## What not to do
- Do not paste customer PII into internal notes unnecessarily.
- Do not try to “fix” automation by editing live templates without going through the template governance process.
- Do not disable automation for a single ticket by “closing it” (auto-close is disallowed).

---

## Training checklist (recommended)
- [ ] Agent understands what routing tags mean
- [ ] Agent knows how to override routing + apply feedback tags
- [ ] Agent knows how to escalate to on-call for SEV-0 issues
- [ ] Agent knows chargebacks and shipping exceptions playbooks
- [ ] Agent understands “automation is assistive; humans remain responsible”

