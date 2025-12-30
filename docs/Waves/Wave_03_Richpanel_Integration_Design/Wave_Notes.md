# Wave 03 — Richpanel Integration Design (Notes)

Last updated: 2025-12-22  
Status: **Complete (tenant verification deferred)**

## Wave goal
Define the exact **Richpanel → Middleware** integration contract and the target Richpanel configuration required for:
- safe routing to the correct department
- safe FAQ automation (with confidence gating + deterministic identity checks)
- no routing loops / duplicates / “routing fights” with legacy automations

---



## Deferred tenant verification (not blocking)
Per your instruction, we are **holding off** on Richpanel tenant/UI verification for now.

- The verification checklist remains documented in:
  - `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Tasks.md`
  - `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Quick_Checklist_Plain_English.md`

The Wave 03 design is **safe to proceed** without these checks because we have robust fallbacks:
- trigger can live in Assignment Rules if Tagging Rules cannot call HTTP Target
- webhook payload can be minimal (ticket_id only) with follow-up API reads
- webhook auth can be a token in URL path/body if custom headers are not supported
- order-status auto-replies are gated by deterministic order linkage; otherwise we ask for order #

## Key finding from your current Richpanel setup (high-impact)
Your workspace contains automations that use:
- **Skip all subsequent rules = ON**
- **Reassign even if already assigned = ON**
- triggers on new conversation and/or new customer message

This is a common source of issues in middleware projects:
- the middleware trigger rule may **never fire** if placed below a “skip subsequent rules” rule
- routing can be overridden later (routing fights) if legacy rules keep reassigning

Wave 03 documentation now treats this as a first-class design constraint.

---

## Clarification (so we don’t get stuck)
You do **not** need to know the answers to Richpanel tenant capability questions.

We will proceed using **best-suggested defaults** and we assign verification to Cursor agents.

### Where the verification lives
- 1-page summary: `Cursor_Agent_Quick_Checklist_Plain_English.md`
- Full task list: `Cursor_Agent_Tasks.md`
- Explanation + fallbacks: `docs/03_Richpanel_Integration/Tenant_Capabilities_Clarifications.md`

---

## What Wave 03 will produce (deliverables)
- Richpanel trigger design (HTTP Target/webhook), placement strategy, and loop-prevention
- Tag taxonomy (`route-*`, `mw-*`) and mapping to departments/teams
- Richpanel automation changes required (disable/guard legacy rules)
- Richpanel API contracts (tickets/tags/teams/orders) + error handling + rate limiting
- Integration test plan for staging + “dry run” rollout plan

---

## Documents updated/created in this wave
- `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
- `docs/03_Richpanel_Integration/Automation_Rules_and_Config_Inventory.md`
- `docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md`
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`
- `docs/03_Richpanel_Integration/Tenant_Capabilities_Clarifications.md`
- `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Tasks.md`
- `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Quick_Checklist_Plain_English.md`
