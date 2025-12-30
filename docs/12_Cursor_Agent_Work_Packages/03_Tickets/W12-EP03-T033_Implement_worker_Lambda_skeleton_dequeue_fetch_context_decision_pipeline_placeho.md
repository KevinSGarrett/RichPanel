# W12-EP03-T033 — Implement worker Lambda skeleton (dequeue, fetch context, decision pipeline placeholder, action stub)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Process queued events reliably and prepare for routing/automation logic.

## Context / References
- `docs/02_System_Architecture/Data_Flow_and_Storage.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`

## Dependencies
- W12-EP03-T030
- W12-EP03-T031
- W12-EP03-T032

## Implementation steps
1. Consume SQS messages and enforce idempotency at worker layer.
1. Fetch ticket context from Richpanel APIs (or stub).
1. Run placeholder decision pipeline that defaults to route-only until LLM + templates added.
1. Write observability events for each major step.

## Acceptance criteria
- [ ] Worker processes messages without crashing on transient failures (retry safe).
- [ ] Route-only safe fallback works (no customer replies yet).
- [ ] All actions are idempotent.

## Test plan
- Integration test with stubbed Richpanel client.
- DLQ behavior verified for hard failures.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
