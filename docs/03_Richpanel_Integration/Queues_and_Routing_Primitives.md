# Queues and Routing Primitives (Richpanel)

Last updated: 2025-12-21
Last verified: 2025-12-21 — Updated to v1 `route-*` tag strategy and Chargebacks/Disputes queue naming.

This doc defines the **building blocks** we can use in Richpanel to implement routing and automation safely.

It exists because “department” can mean different things in practice:
- a Richpanel **Team** (organizational unit)
- a “virtual queue” (Tag + Saved View + Assignment Rule)
- a **Channel** (Email / Livechat / TikTok / Social)
- an **assignee** (individual agent)

We need a clear strategy so the middleware doesn’t create fragile behavior.

---

## 1) Routing primitives (what we should use)

### 1.1 Tags (primary routing primitive)
**Recommendation:** The middleware should apply **routing tags** as its primary action.

Why:
- tags are stable across changes to teams and staffing
- tags can drive existing Richpanel automations (assignment rules, SLAs, views)
- tags help analytics (“what was this ticket about?”)

Example tags (illustrative):
- `intent_order_status`
- `intent_return_request`
- `intent_shipping_exception_dnr`
- `intent_route-chargebacks-disputes`

### 1.2 Teams (for sensitive / dedicated workflows)
Use Teams when:
- the workflow is high-risk (financial/legal)
- you need restricted access and clean reporting
- you want explicit ownership

✅ Decision: create a dedicated **Chargebacks / Disputes** Team.

### 1.3 Saved Views (“virtual queues”)
Use when you want queue-like behavior without creating a new Team:
- Tag + Saved View + Assignment Rule

We can still use this pattern for lower-risk queues (e.g., “Promotions inquiries”) if desired.

### 1.4 Direct assignment to agent (use sparingly)
Use only when:
- you have strict coverage rules (round-robin/balanced)
- you need to force ownership for time-sensitive issues

---

## 2) Chargebacks / Disputes queue (implementation notes)

### 2.1 Why this queue is special
Chargebacks/disputes are:
- high-risk (financial + legal + fraud)
- non-standard customer support
- often require restricted access and a consistent playbook

✅ Policy: **Tier 0** — no auto-resolution, no automated promises.

### 2.2 Recommended Richpanel setup steps
1) Create a Richpanel Team:
   - Name: **Chargebacks / Disputes**
2) Create (or reuse) a routing tag:
   - Recommended: `route-chargebacks-disputes`
   - Note: your current tag list already includes tags like `chargeback-lost`, `chargeback-inprocess`, `chargeback-won` (from your current setup snapshot). We can keep those as outcome tags while using `route-chargebacks-disputes` as the routing tag.
3) Create an assignment rule:
   - If tag contains `route-chargebacks-disputes` → assign to Chargebacks/Disputes Team (or a dedicated view)
4) Disable/modify conflicting existing automations:
   - Your current setup includes automation rules that **auto-close** chargeback subjects (see `rp.current-setup.automation.rule.auto-close-chargeback-subject` and `rp.current-setup.automation.rule.chargeback-auto-close` in your snapshot).
   - This conflicts with our hard constraint: **middleware never auto-closes** (and chargebacks should not be auto-closed either).
   - Plan: replace auto-close with “tag + route” behavior.

### 2.3 Middleware behavior
When the model detects chargeback/dispute (confidence ≥ threshold):
- Apply tag `route-chargebacks-disputes`
- Add internal note with classification result
- Route/assign according to your Richpanel rules
- Do **not** auto-reply except possibly a neutral acknowledgement template (optional and only if you want it)

---

## 3) Shipping exceptions ownership (“keep it simple” rollout)
✅ Decision: shipping exceptions → **Returns Admin** queue for early rollout.

Includes:
- missing items
- incorrect items
- damaged in transit
- lost in transit
- delivered-but-not-received (DNR)

Rationale:
- reduces cross-team handoffs early
- centralizes policy decisions (refund/reship/claim)
- can be refactored later into a dedicated Shipping/Claims team without changing the intent taxonomy

---

## 4) Drift management
Because teams/tags change over time:
- build a “mapping snapshot” job (weekly) to fetch Teams + Tags and compare to expected
- alert if a required Team/Tag is missing or renamed

See:
- `docs/03_Richpanel_Integration/Team_Tag_Mapping_and_Drift.md`
