# Run 03 — Richpanel Integration + Action Executor (EP04)

## Tickets targeted
- W12-EP04-T040 (ops task can be done separately)
- W12-EP04-T041
- W12-EP04-T042
- W12-EP04-T043
- W12-EP04-T044

## Prompt (copy/paste)
Implement Richpanel integration and an action executor with action-level idempotency.
Constraints:
- Auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) tickets.
- Avoid webhook loops (mw-routing-applied guard).
- Respect rate limits and Retry-After.
- No raw customer message bodies in logs.

Deliverables:
- Richpanel client library + tests
- Action executor + idempotency
- Staging integration test harness (if staging access exists)
