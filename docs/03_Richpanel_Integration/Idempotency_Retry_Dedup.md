# Idempotency, Retries, and Deduplication

Last updated: 2025-12-21
Last verified: 2025-12-21 — Expanded v1 rules and DynamoDB-backed idempotency design.

This document defines **non-negotiable** reliability behavior for the middleware.
It exists because webhook/event systems will inevitably deliver duplicates, reorder events, or fail intermittently.

Related docs:
- DynamoDB schema: `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
- Rate limiting + retries: `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`
- Common issues reference: `CommonIssues.zip` (see `03-idempotency-duplicate-events.md`, `04-webhook-timeouts-ack-fast.md`, `12-http-target-no-retry.md`)

---

## 1) Requirements (must be true in production)

1) Duplicate inbound events MUST NOT cause:
   - double auto-replies
   - double routing / team bouncing
   - duplicate tag additions that trigger loops

2) Retries MUST be safe:
   - internal retries
   - downstream retries (429)
   - operator retries (manual replay)

3) The system MUST be robust even if:
   - Richpanel does not retry webhook delivery (assume it might not)
   - Richpanel triggers multiple rules for the same underlying message

---

## 2) What we treat as “the same event” (idempotency boundary)

### 2.1 Preferred boundary: inbound customer message ID
Best case: Richpanel payload includes a stable per-message identifier.
Then:
- `event_idempotency_key = evt:rp:{conversation_id}:{customer_message_id}`

### 2.2 Fallback boundary: deterministic hash
If a stable message ID is missing, we use:
- conversation_id
- normalized text
- a time bucket (to reduce accidental collisions while preventing duplicates)

Example:
- `evt:rp:{conversation_id}:{sha256(normalized_text + created_at_bucket)}`

> Warning: this is less perfect than a real message ID.
> It should be treated as a temporary workaround until we confirm the Richpanel payload fields.

---

## 3) Where idempotency is enforced

### 3.1 Ingress (before ACK)
Ingress MUST:
1) validate request
2) compute idempotency key
3) **persist idempotency record** (DynamoDB conditional write)
4) enqueue to SQS
5) return 200 quickly

If step (3) fails because the key already exists:
- return 200
- do not enqueue again

### 3.2 Worker (before side effects)
Worker MUST enforce idempotency again at the “action” level, because:
- the same event may be reprocessed (retries)
- multiple distinct events may attempt the same side effect

Action idempotency keys (examples):
- `act:rp_reply:{conversation_id}:{event_key_suffix}`
- `act:rp_tag:{conversation_id}:{tag}:{event_key_suffix}`
- `act:rp_assign:{conversation_id}:{team}:{event_key_suffix}`

---

## 4) Deduplication vs ordering

### 4.1 Ordering (recommended)
We process per conversation sequentially using:
- SQS FIFO with `MessageGroupId = conversation_id`

This reduces:
- state races
- “team bouncing”
- inconsistent pending-flow behavior

### 4.2 Dedup window (note)
SQS FIFO deduplication can only help within its limited dedup window.
Therefore, DynamoDB idempotency remains required.

---

## 5) Retry strategy (v1)

### 5.1 What we retry automatically
Retry only **transient** errors:
- 429 rate limits
- 5xx from Richpanel/OpenAI/Shopify
- network timeouts

### 5.2 What we do NOT retry blindly
Do not blindly retry if the error suggests a permanent problem:
- 4xx auth/permission errors (401/403)
- validation errors (400/422)
- payload missing required fields (unless we can fetch them from Richpanel)

Instead:
- route to human (safe fallback)
- record error for investigation
- send to DLQ if stuck

### 5.3 Backoff with jitter
- exponential backoff
- honor `Retry-After` when present
- jitter to avoid thundering herd

(See: `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`.)

---

## 6) “Never lose a message” pattern (assumption)
We design as if:
- Richpanel might *not* retry webhook delivery
- We might deploy at the wrong time
- Downstream might be briefly unavailable

Therefore:
- ingest quickly into a durable queue
- maintain internal retry + DLQ
- optionally run a reconciliation job later (Wave 10) to detect “missing processed tag” tickets

---

## 7) Kill switch + shadow mode (recommended)
To prevent incidents:
- **Kill switch**: env flag disables all side-effect actions (replies/tagging/assignment) instantly
- **Shadow mode**: compute decisions but do not act (log only)

These are referenced in:
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`

