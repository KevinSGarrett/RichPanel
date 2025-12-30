# Run 02 — Core Middleware Pipeline (EP03)

## Tickets targeted
- W12-EP03-T030
- W12-EP03-T031
- W12-EP03-T032
- W12-EP03-T033
- W12-EP03-T034
- W12-EP03-T035
- W12-EP03-T036

## Prompt (copy/paste)
Implement the core serverless pipeline per the above tickets.
Key constraints:
- Ingress must ACK fast (<500ms p95 target) by enqueueing to SQS.
- Worker must be idempotent and fail closed (route-only fallback; no automation yet).
- Implement structured observability logs (schema-valid) and correlation IDs.

Deliverables:
- Working ingress + queue + worker skeleton in dev
- Unit tests for validation/idempotency
- Alarm stubs (DLQ, queue age)
- Run report + how to test locally and in AWS dev
