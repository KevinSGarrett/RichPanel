# API Reference (System)

Last verified: 2025-12-29 — Wave F05 (placeholder API surface defined).

This is the canonical human-readable reference for the system’s API surface.
The **machine-readable** source of truth is `docs/04_API_Contracts/openapi.yaml`.

## Status
- Foundation mode: endpoints below are **planned** and may change.
- When build starts: keep this doc in sync with actual deployed endpoints and `openapi.yaml`.

## Endpoints (planned)

### POST /webhooks/richpanel
**Purpose:** Receive Richpanel events (ticket created/updated, message received, etc.), validate, ACK fast, and enqueue for processing.

**References**
- Implementation design: `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
- Security controls: `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`

**Behavior**
- Validate signature / secret (exact method TBD by integration requirements)
- Validate required fields
- Persist idempotency key (planned)
- Enqueue message to SQS FIFO
- Return 2xx quickly

### GET /health
**Purpose:** Liveness check for infra/runtime.

### GET /ready
**Purpose:** Readiness check (optional; may be merged into /health for Lambda).

## API change rules
Any time an endpoint changes, update:
- `docs/04_API_Contracts/openapi.yaml`
- `docs/02_System_Architecture/System_Matrix.md`
- `CHANGELOG.md`
- Add test evidence entry in `docs/08_Testing_Quality/Test_Evidence_Log.md` (when tests exist)
