# Webhook Authentication and Request Validation

Last updated: 2025-12-22

This document defines the security model for inbound triggers from **Richpanel → middleware**.

Design goals:
- prevent unauthorized callers from triggering actions
- reduce replay/spam risk
- fail closed safely without breaking support operations

---

## 1) Threats we must defend against

1) **Spoofed webhook**: attacker calls our endpoint and causes routing changes or automated replies.
2) **Replay**: attacker replays a valid request to spam actions.
3) **Payload tampering**: attacker modifies request body fields.
4) **Abuse / DoS**: floods endpoint to exhaust concurrency and costs.
5) **Schema confusion**: malformed payload causes crashes or mis-parsing.

---

## 2) Required baseline (always, regardless of auth method)

These controls apply to *every* request:

### 2.1 Strict request validation (required)
- Require `Content-Type: application/json`
- Parse JSON strictly (reject invalid JSON with 400)
- Validate against a minimal schema:
  - required: `ticket_id` (or `conversation_id`)
  - required: `event_type` (string)
  - optional: `message_id` (string) if available
- Reject unknown/oversized payloads (hard max body size)

### 2.2 Idempotency (required)
- Compute an idempotency key per event (prefer message id; else hash of ticket_id + event timestamp).
- Use conditional writes to prevent duplicate processing.

### 2.3 Throttling / abuse protection (required)
- API Gateway throttling must be enabled.
- AWS WAF rate-based rule is recommended in prod.

---

## 3) Authentication options (tiered)

Richpanel tenant capabilities may vary, so we document a tiered approach.

### Option A (best): HMAC signature + timestamp
**Requires** Richpanel to send:
- `X-Signature: <hmac_sha256(secret, timestamp + "." + raw_body)>`
- `X-Timestamp: <unix seconds>`

Middleware validation:
- reject if timestamp older than 5 minutes
- compute HMAC and compare in constant time
- (optional) reject if timestamp too far in the future

Replay resistance:
- timestamps + short window reduce replay risk
- idempotency table still required

### Option B (recommended v1): Static secret header token
**Requires** Richpanel to send:
- `X-Middleware-Token: <random static secret>`

Middleware validation:
- reject if missing/incorrect (401)
- still enforce idempotency + throttling

Replay resistance:
- token alone does not prevent replay, so idempotency is essential.

### Option C (fallback only): URL token (path or query)
Example:
- `POST /webhook/<token>` or `POST /webhook?token=<token>`

Risks:
- token may appear in logs or shared URLs if misconfigured
- still acceptable as a last resort if headers are not supported

---

## 4) Recommended v1 selection

Until tenant verification confirms HMAC support, use:

✅ **Option B: static header token**  
PLUS:
- API throttling
- WAF rate-based rule (prod)
- request schema validation
- idempotency

---

## 5) Error handling requirements

- 401: auth failure (do not reveal which part failed)
- 400: invalid JSON / missing required fields
- 2xx: accepted + enqueued (ACK-fast pattern)
- 5xx: only for true internal errors (should be rare)

Important:
- ACK must not depend on OpenAI/Richpanel/Shopify calls.
- ACK should happen after durable enqueue (SQS) or durable store (DynamoDB) to avoid lost events.

---

## 6) Logging requirements (PII-safe)

Log only:
- request id / correlation id
- ticket_id
- event_type
- auth_method (A/B/C)
- auth_result (pass/fail)
- decision: enqueued vs rejected

Do **not** log:
- header token value
- raw message body
- raw payload beyond minimal metadata

---

## 7) Testing requirements (v1)

- Unit tests: auth pass/fail for chosen method
- Unit tests: schema validation rejects invalid payloads
- Integration test: duplicate event is de-duped
- Load test: throttling works; WAF rule triggers (prod optional)

