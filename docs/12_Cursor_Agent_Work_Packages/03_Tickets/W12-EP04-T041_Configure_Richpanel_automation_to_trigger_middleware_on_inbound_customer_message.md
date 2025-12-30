# W12-EP04-T041 — Configure Richpanel automation to trigger middleware on inbound customer messages (avoid loops)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Ops (Richpanel Admin) + Backend

## Objective
Trigger middleware reliably without re-triggering on middleware messages or assignments.

## Context / References
- `docs/03_Richpanel_Integration/Automation_Rules_and_Config_Inventory.md`
- `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
- `docs/03_Richpanel_Integration/Idempotency_Retry_Dedup.md`

## Dependencies
- W12-EP04-T040
- W12-EP03-T030

## Implementation steps
1. Create automation rule: when customer sends a message → call HTTP Target (middleware endpoint).
1. Include minimal payload (ticket_id) unless tenant confirms safe message templating.
1. Add guard condition: do not trigger if `mw-routing-applied` tag already present (if supported).
1. Ensure rule ordering prevents skip-subsequent-rules blocking.

## Acceptance criteria
- [ ] Inbound customer message triggers middleware once.
- [ ] Middleware-generated messages do not re-trigger.
- [ ] Guard prevents repeated triggers on the same ticket.

## Test plan
- (TBD)

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
