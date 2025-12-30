# W12-EP03-T030 — Implement API Gateway + ingress Lambda (fast ACK, validation, enqueue)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Receive Richpanel triggers safely, validate, and enqueue to SQS within latency target.

## Context / References
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- `docs/02_System_Architecture/Data_Flow_and_Storage.md`
- `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
- `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`

## Dependencies
- W12-EP02-T020
- W12-EP01-T013

## Implementation steps
1. Create HTTP endpoint and ingress handler that validates auth token and request schema.
1. Normalize into internal event format with `ticket_id`, `event_type`, timestamps, and idempotency key.
1. Write idempotency record (conditional) and enqueue message to SQS FIFO.
1. Return 2xx quickly (<500ms p95) regardless of downstream processing.

## Acceptance criteria
- [ ] Ingress returns 2xx quickly after enqueue.
- [ ] Invalid/unauthenticated requests rejected and logged (without PII).
- [ ] Duplicate webhook deliveries do not enqueue duplicates (idempotency).

## Test plan
- Unit tests for request validation and idempotency key generation.
- Integration test: send same webhook twice; only one message processed.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- No raw message text logged at ingress.
- Auth token validated before processing.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
