# W12-EP04-T042 — Implement Richpanel API client with retries, pagination, and rate-limit handling

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Reliable Richpanel API access for ticket context, tag operations, team list, and order lookups.

## Context / References
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`
- `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`

## Dependencies
- W12-EP03-T036
- W12-EP00-T001

## Implementation steps
1. Implement client methods needed by the pipeline: get ticket, add/remove tags, list tags, list teams, post message, order endpoints.
1. Implement consistent error mapping and retry/backoff rules.
1. Add integration tests using mocked HTTP responses.

## Acceptance criteria
- [ ] Client correctly handles 429 with Retry-After.
- [ ] Client methods are unit-tested.
- [ ] No PII is logged from raw payloads.

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
