# W12-EP03-T032 — Create DynamoDB tables for idempotency + minimal conversation state with TTL

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend/Infra

## Objective
Persist minimal state required to prevent duplicates and track automation constraints.

## Context / References
- `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
- `docs/06_Security_Privacy_Compliance/Data_Retention_and_Access.md`

## Dependencies
- W12-EP02-T020

## Implementation steps
1. Create `rp_mw_idempotency` table with conditional writes and TTL.
1. Create `rp_mw_conversation_state` table with TTL and minimal fields (last_action, last_template, etc.).
1. Add optional PITR configuration per policy.
1. Document TTL values and rationale.

## Acceptance criteria
- [ ] Tables exist with encryption and TTL.
- [ ] Idempotency conditional write behavior tested.

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
