# W12-EP03-T031 — Provision SQS FIFO + DLQ and internal message schema (conversation-ordered processing)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend/Infra

## Objective
Ensure in-order processing per ticket and safe DLQ handling.

## Context / References
- `docs/07_Reliability_Scaling/SQS_FIFO_Strategy_and_Limits.md`
- `docs/02_System_Architecture/Sequence_Diagrams.md`

## Dependencies
- W12-EP02-T020

## Implementation steps
1. Create FIFO queue with DLQ and redrive policy.
1. Define MessageGroupId = ticket_id; define deduplication strategy.
1. Document maximum receive count and visibility timeout per defaults.
1. Add CloudWatch alarms for DLQ > 0 and oldest message age thresholds.

## Acceptance criteria
- [ ] FIFO queue exists with DLQ.
- [ ] Alarms configured.
- [ ] Message schema documented and validated.

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
