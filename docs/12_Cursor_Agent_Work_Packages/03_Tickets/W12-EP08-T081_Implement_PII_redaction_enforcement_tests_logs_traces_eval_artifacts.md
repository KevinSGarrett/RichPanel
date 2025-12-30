# W12-EP08-T081 — Implement PII redaction enforcement + tests (logs, traces, eval artifacts)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend/SecOps

## Objective
Ensure no sensitive customer data leaks into logs or artifacts.

## Context / References
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`
- `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`

## Dependencies
- W12-EP03-T035

## Implementation steps
1. Implement redaction utilities for email/phone/order#/tracking.
1. Ensure logging pipeline uses redacted fields only.
1. Add unit tests verifying redaction on representative samples.

## Acceptance criteria
- [ ] PII redaction tests pass.
- [ ] No raw message bodies stored in DynamoDB or logs by default.

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
