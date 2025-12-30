# Wave 1 — Discovery & requirements baseline

Last updated: 2025-12-21
Last verified: 2025-12-21 — Updated with confirmed queue ownership and routing mechanics.

## Goals
1) Convert the high-level idea into **testable requirements** (functional + non-functional).
2) Define an **intent taxonomy v0.1** and map it to destination **queues/teams**.
3) Establish **automation policy** (auto-send vs draft vs route-only) with clear risk tiers.
4) Capture unknowns (identifiers, triggers, order lookup) in a way that engineering can still build safely.

---

## Key inputs reviewed
- Department list (10 teams)
- RoughDraft: top FAQs and recommended departmental ownership
- CommonIssues checklist (loops, spoofing, idempotency, rate limits, etc.)
- SC_Data dataset (3,613 conversations / 28,585 messages) — used only in aggregate

---

## Decisions captured (Wave 01)
- ✅ Two-layer routing model: intent taxonomy → queue/team
- ✅ Risk-tiered automation policy (Tier 0–3)
- ✅ Tracking link + tracking number allowed in order-status auto-replies when deterministic match exists
- ✅ Middleware must **auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)** tickets
- ✅ Chargebacks/disputes route to dedicated chargeback/dispute queue (Tier 0)

Confirmed defaults:
- ✅ Create Chargebacks/Disputes Team/queue (Tier 0; no automation)
- ✅ Missing items / shipping exceptions → Returns Admin (“Fulfillment Exceptions / Claims”)
- ✅ Delivered-but-not-received → Tier 1 safe assist + route to human (no auto-resolve)
- ✅ Richpanel routing implementation: use routing tags + Richpanel assignment automations/views (tickets assigned to agents via `assignee_id`)

---

## Deliverables updated/produced in Wave 01
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- `docs/01_Product_Scope_Requirements/FAQ_Automation_Scope.md`
- `docs/01_Product_Scope_Requirements/Customer_Message_Dataset_Insights.md`
- `docs/03_Richpanel_Integration/Queues_and_Routing_Primitives.md`
- Integration notes updated:
  - `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
  - `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`

---

## Remaining open items (carry into Wave 03 / Wave 05)
- Confirm the exact Richpanel trigger mechanism and inbound payload schema
- Confirm how to implement team routing in your tenant (tags + assignment rules vs other)
- Confirm identifier availability in payloads (email, phone, order number)
- Confirm whether Richpanel Order APIs provide tracking fields we need
- Confirm Shopify Admin API access for fallback order lookup

---

## Wave 01 status
✅ **Complete enough to proceed to Wave 02 (Architecture)**, with the above open items tracked.
