# W12-EP07-T074 — Enforce controlled auto-close policy (whitelist + audit)

Last updated: 2025-12-29

## Owner / Agent (suggested)
Backend + Richpanel config

## Objective
Implement the v1 invariant:

- Default: middleware does **not** auto-close tickets.
- Exception: middleware may set a ticket to **Resolved** only when:
  - the selected Tier 2 `template_id` is explicitly whitelisted for auto-close, and
  - gating passes, and
  - the customer message includes reply-to-reopen language.

Tier 0 / high-risk intents must never be auto-closed.

## Context / References
- `docs/00_Project_Admin/Change_Requests/CR-001_NoTracking_Delivery_Estimates.md`
- `docs/01_Product_Scope_Requirements/FAQ_Automation_Scope.md`
- `docs/05_FAQ_Automation/Human_Handoff_and_Escalation.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/03_Richpanel_Integration/Automation_Rules_and_Config_Inventory.md`

## Dependencies
- W12-EP04-T043 (routing + deterministic match)
- W12-EP05-T061 (template renderer / config loader)

## Scope
1) Add an **auto-close allowlist** (config) for template IDs.
2) Add a guard so any attempt to resolve a ticket:
   - is blocked if `template_id` is not in allowlist, or
   - is blocked if Tier 2 gating fails, or
   - is blocked if the situation is “late/out-of-window” (CR-001 rule).
3) Ensure Richpanel-side automations do not auto-close on tags/subjects (all closes should be initiated by middleware and auditable).
4) Emit an audit log entry for any resolved ticket (inputs + reason).

## Acceptance criteria
- Non-allowlisted template IDs never resolve tickets automatically.
- Allowlisted template (`t_order_eta_no_tracking_verified`) resolves the ticket only when:
  - Tier 2 deterministic match is true,
  - order is within SLA window,
  - confidence thresholds pass,
  - tags include `mw:auto_closed` and `mw:deflected`.
- Any Tier 0 flagged conversation remains open and routes to a human.
- Unit + integration tests demonstrate the above and produce concrete proof (test output stored per run).

## Implementation steps
- [ ] Add config: `AUTO_CLOSE_TEMPLATE_ALLOWLIST = ["t_order_eta_no_tracking_verified"]`
- [ ] Implement `is_auto_close_allowed(template_id, context)` utility
- [ ] Add middleware guard before any Richpanel “resolve/close” action
- [ ] Add logging: `auto_close_decision` event with decision trace
- [ ] Add tests:
  - allowlisted template resolves (happy path)
  - non-allowlisted template does not resolve
  - allowlisted template late/out-of-window -> no resolve + route
- [ ] Update docs referencing auto-close behavior and keep them in sync

## Notes
Auto-close should set status to **Resolved** (not permanently closed) so a customer reply can reopen the ticket.
