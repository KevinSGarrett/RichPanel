# W12-EP03-T035 — Implement observability event logging + correlation IDs (ingress and worker)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Make every request traceable across ingress→queue→worker→actions.

## Context / References
- `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`
- `docs/08_Observability_Analytics/Tracing_and_Correlation.md`

## Dependencies
- W12-EP03-T030
- W12-EP03-T033

## Implementation steps
1. Generate or propagate `correlation_id` from ingress to worker.
1. Emit structured logs matching v1 schema for ingress_received, enqueued, worker_started, decision_made, action_applied.
1. Validate log schema in unit tests.

## Acceptance criteria
- [ ] All logs include ticket_id and correlation_id.
- [ ] Schema validation passes in CI.

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
