# W12-EP03-T036 — Implement vendor retry/backoff utilities and concurrency bounds (prevent rate-limit storms)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Prevent unbounded retries and protect vendors (Richpanel/OpenAI/Shopify).

## Context / References
- `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`
- `docs/07_Reliability_Scaling/Resilience_Patterns_and_Timeouts.md`

## Dependencies
- W12-EP03-T033

## Implementation steps
1. Implement standardized retry wrapper respecting `Retry-After` when present.
1. Implement exponential backoff with jitter and maximum attempts.
1. Enforce per-vendor concurrency caps if needed (config-driven).
1. Emit metrics for rate-limit events.

## Acceptance criteria
- [ ] 429 storms do not cause runaway retries.
- [ ] Retries are bounded and observable.

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
