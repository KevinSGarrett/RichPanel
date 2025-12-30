# SQS FIFO Strategy and Limits

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

We use an AWS SQS queue as the durable buffer between:
- Richpanel → middleware ingress (ACK fast)
- middleware worker processing (OpenAI + Richpanel writes)

This doc explains why we propose **SQS FIFO** for v1 and when to switch to Standard.

---

## 1) Why FIFO is the default for v1

### 1.1 Per-conversation ordering matters
For a given conversation/ticket, multiple customer messages can arrive quickly.
If we process them out of order, we can cause:
- incorrect routing (second message clarifies intent, but first routes incorrectly after)
- duplicate or contradictory auto-replies
- tag thrashing (team assignments toggling)

FIFO supports ordering within a group.

### 1.2 We can get ordering without sacrificing global throughput
We group by conversation:

- `MessageGroupId = conversation_id`

This means:
- messages in the same conversation process sequentially
- different conversations can process concurrently

### 1.3 Our observed traffic is well within FIFO limits
Even the observed peak (~430/hour) is extremely low relative to FIFO throughput.
So FIFO’s stricter semantics are worth the simplicity and safety.

---

## 2) How we use FIFO safely

### 2.1 Deduplication strategy
Prefer:
- `MessageDeduplicationId = richpanel_message_id` (if we have it)

Fallback:
- hash of `(ticket_id + message_created_at + message_text_hash)`  
  (must be stable and collision-resistant enough for our volume)

**Important:** FIFO dedup is a convenience; **it is not sufficient alone.**  
We still implement DynamoDB idempotency (authoritative).

### 2.2 Visibility timeout and retries
- Set visibility timeout to 2–5× the p99 worker execution time.
- Use DLQ redrive after 3–5 failed receives.

Why:
- prevents poison messages from blocking the queue
- keeps retries bounded and observable

### 2.3 One-message worker execution policy (v1)
We process 1 SQS message at a time per Lambda invocation (batch size = 1) in v1.

Rationale:
- simplifies idempotency + partial side effect handling
- easier failure isolation
- good fit for modest volumes

We can later use batching to reduce cost if needed.

---

## 3) When FIFO is no longer the best choice

Switch to **SQS Standard** if any of the following are true:
- we need extremely high throughput and FIFO becomes a bottleneck
- strict ordering is no longer required (or handled in another layer)
- we want higher parallelism without group-level constraints

If we switch to Standard:
- idempotency becomes even more critical
- we must enforce per-conversation “single-flight” ourselves (e.g., DynamoDB locks)

---

## 4) Migration plan (FIFO → Standard) if needed
This is a future-proofing note; we do not plan to do this in v1.

Steps:
1) Create new Standard queue
2) Update ingress to publish to the new queue (dual-write optional)
3) Update worker trigger to read Standard queue
4) Add per-conversation lock (DynamoDB conditional write lock)
5) Drain FIFO queue; turn it off after backlog clears

---

## 5) Go-live checklist (FIFO-specific)
- Confirm we have a stable `conversation_id` for MessageGroupId
- Confirm we have a stable message-id or a safe fallback for dedup IDs
- Confirm DLQ alarms exist
- Confirm worker reserved concurrency is set and tested
