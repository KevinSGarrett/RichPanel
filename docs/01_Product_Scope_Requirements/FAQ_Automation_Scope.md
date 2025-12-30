# FAQ Automation Scope (Top FAQs)

Last updated: 2025-12-29
Last verified: 2025-12-29 — Updated with confirmed policies (shipping exceptions, chargebacks, DNR).

This document defines:
- which customer FAQs we will automate vs route-only
- **how** automation is allowed to respond (risk-tiered policy)
- the rollout plan so we don’t create production issues (wrong replies, privacy leaks, loops)

Inputs used:
- `RoughDraft/Top_10_FAQ.txt` + `RoughDraft/SC_Top_FAQs_Summary.csv`
- `SC_Data_ai_ready_package.zip` (real recent conversations; used only in aggregate)

---

## 1) Guiding principle
Automation should reduce workload **without increasing risk**.

The biggest failure modes we are designing against:
- sending the wrong customer order info (privacy + trust impact)
- replying when the customer is angry/escalating (makes things worse)
- causing webhook/automation loops
- over-automating edge cases (refunds, disputes) that require policy judgment

---

## 2) Automation tiers (policy)
### Tier 0 — Never auto-send
Only route + tag + internal notes.
Examples:
- chargebacks/disputes
- legal complaints
- harassment/threats
- suspected fraud

### Tier 1 — Safe assist message + route (allowed)
Send a **generic** message that:
- asks for missing info, OR
- provides non-account-specific next steps

No refunds/reships. No private details.

### Tier 2 — Verified auto-reply (allowed)
Send an account/order-specific reply **only when we have deterministic match**.

You approved:
- include **tracking link + tracking number** when match is deterministic

### Tier 3 — Auto-actions (not in early rollout)
Refunds, cancellations, address changes, exchanges, reships.
These are high-risk and should be deferred until after we have:
- strong identity verification
- policy guardrails
- audit logging
- human override tooling

---

## 3) Top FAQ list (from RoughDraft summary)
Unit: tickets and % of all tickets (approx. 3.6k in sample)

Top intents (examples):
- Order status & tracking — ~52% of tickets
- Cancel order — ~6.6%
- Product/app troubleshooting — ~4.8%
- Cancel subscription — ~3.9%
- Missing items in shipment — ~3.5%
- Shipping delay / not shipped — ~3.2%
- Return / exchange / refund — ~2.4%
- Chargeback / dispute — ~2.4% (high-risk)

This confirms our early automation focus:
- **Order status & tracking** first
- everything else primarily route/tag + safe assist (Tier 1) until proven safe

---

## 4) Phase plan (recommended rollout)
### Phase A (MVP automation)
1) **Order status & tracking** (Tier 2 when verified, else Tier 1)
2) **Shipping delay / not shipped** (Tier 2 when verified, else Tier 1)

### Phase B (MVP+)
- “Cancel order” as route + intake (Tier 1), not auto-cancel
- “Missing items in shipment” as route + intake (Tier 1), not auto-reship
- “Returns/refunds” as policy-aware intake + agent-draft (Tier 1 / draft-for-agent)

### Phase C (later / optional)
- subscription management automation (if subscription system/API access is confirmed)
- limited cancellation automation only if policy window + fulfillment status are deterministic

---

## 5) Order status automation — identity verification (required)
We only disclose order-specific info if:
1) we can match exactly **one** order with high confidence, and
2) the match is supported by at least one of:
   - order number extracted from message and verified in the order system
   - conversation email matches order email
   - conversation phone matches order phone (normalized)

If we cannot verify deterministically:
- do not include tracking number/link
- send Tier 1 message asking for order number or email

**Do not include in automated replies**
- shipping address
- payment method info
- internal fraud/chargeback notes

---

## 6) Delivered but not received (approved default)

Confirmed policy:
- Always route to a human queue (Returns Admin / Shipping Claims).
- Also send a Tier 1 “safe assist” message immediately:
  - check neighbors/front desk/mailroom
  - allow up to 24 hours after “delivered”
  - confirm address and best contact method
  - if you have order number, reply with it

If deterministic match exists:
- include tracking link/number (approved)
- still do not promise refund/reship; human decides next steps

Rationale:
- pure routing can feel slow; safe assist reduces follow-ups
- auto-resolving is too risky (fraud + policy variance)

---

## 7) Auto-close policy (approved)

Default rule:
- Do not auto-close tickets from the middleware.

Exception (explicit whitelist):
- Auto-close is allowed only for specific Tier 2 templates that are **deflection-safe** and include reply-to-reopen language.
- Initial whitelist (CR-001):
  - `t_order_eta_no_tracking_verified` (order status when no tracking exists yet and order is within SLA window)

The middleware may:
- add tags
- add internal notes (decision trace)
- send allowed replies (Tier 1/Tier 2)
- mark as **Resolved** only when the template is whitelisted and gating passes

---

## 8) Chargebacks / disputes (Tier 0, escalation routing)
Policy (approved):
- never auto-resolve
- route to dedicated queue (create Team “Chargebacks / Disputes”)
- optional: send a neutral acknowledgement (“We’ve escalated your message to our disputes team.”)

If the team is not yet created in the tenant at go-live:
- route to Leadership Team + tag `needs_chargeback_queue` (temporary contingency)

---

## 9) What remains open (Wave 03/Wave 05 confirmations)
- Confirm the exact order data access method for automation:
  - Richpanel Order APIs vs direct Shopify Admin API
- Confirm whether we can route by Team vs tag-based virtual queues in your tenant
- Confirm subscription system/source-of-truth (for future automation)
