# W12-EP04-T043 — Implement action executor (route/tag/assign/reply) with action-level idempotency keys

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Apply actions exactly-once despite retries and partial failures.

## Context / References
- `docs/03_Richpanel_Integration/Idempotency_Retry_Dedup.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

## Dependencies
- W12-EP03-T032
- W12-EP04-T042

## Implementation steps
1. Define action idempotency keys: (ticket_id, action_type, payload_hash).
1. Before applying an action, write action key in idempotency table (conditional).
1. Apply Richpanel actions (tags, assignment, message).
1. Record success/failure observability events.

## Acceptance criteria
- [ ] Duplicate worker retries do not duplicate messages or tags.
- [ ] Partial failures are recoverable with retries without duplicate side effects.

## Test plan
- Integration: simulate retry after message send; verify no duplicate send.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
