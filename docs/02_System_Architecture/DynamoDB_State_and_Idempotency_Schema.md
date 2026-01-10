# DynamoDB State + Idempotency Schema (Recommended)

Last updated: 2026-01-03

This document defines the **minimal DynamoDB data model** to make the middleware:
- **idempotent** (no double replies / double routing)
- **stateful where needed** (multi-step flows like “please provide your order #”)
- **safe by default** (avoid storing raw message content / PII wherever possible)
- **operationally debuggable** (enough metadata to trace what happened)

> Scope note: This is the *recommended v1 state model*. It is intentionally small.
> If we later need richer analytics/event replay, we add an **encrypted S3 event archive** (Wave 08/10).

---

## 0) Design goals (non-negotiable)

### 0.1 Idempotency everywhere
Every inbound event and every side-effecting action MUST be safe to run multiple times without producing duplicates.

### 0.2 Data minimization
- Do **not** store raw customer message bodies in DynamoDB by default.
- Do **not** store full emails/phones in logs or DynamoDB unless strictly required.
- Prefer:
  - hashes
  - last-4
  - redacted versions
  - short TTLs

### 0.3 TTL-based cleanup
All items MUST have TTL so the system does not accumulate indefinite data.

### 0.4 Environment isolation
Table names MUST be environment-scoped (dev/staging/prod) to avoid cross-environment contamination.

---

## 1) Tables (v1 recommended)

### Table A — `rp_mw_idempotency` (required)
Purpose:
- prevent duplicate processing of the same inbound customer message/event
- prevent duplicate **side effects** (auto-replies, tag updates, assignments)

**Primary key**
- Partition key: `event_id` (string) — canonical event identifier

**Required attributes**
- `created_at` (ISO timestamp)
- `last_processed_at` (ISO timestamp)
- `received_at` (ISO timestamp, from ingress payload if provided)
- `expires_at` (epoch seconds) — TTL attribute
- `status` (string) — `processed` (route-only in v1)
- `mode` (string) — `route_only` | `automation_candidate`
- `conversation_id` (string)
- `safe_mode` (bool)
- `automation_enabled` (bool)
- `source_message_id` (string, optional if missing)
- `payload_sha256` (string) - hex digest of the normalized payload (no body stored)
- `payload_bytes` (number) - size of the normalized payload in bytes
- `intent` (string, optional placeholder)

**Recommended TTL**
- 30 days (tunable; enforced via `expires_at` and Lambda default of 30 days)

#### A.1 Idempotency key formats (recommended)
We use distinct namespaces so we can track both *event idempotency* and *action idempotency*.

Inbound event keys (preferred, if we have a stable message ID):
- `evt:rp:{conversation_id}:{customer_message_id}`

If Richpanel payload does not provide a stable message ID, fall back to a deterministic hash:
- `evt:rp:{conversation_id}:{sha256(normalized_text + created_at_bucket)}`

Action keys:
- `act:rp_reply:{conversation_id}:{customer_message_id or hash}`
- `act:rp_tag:{conversation_id}:{tag_name}:{customer_message_id or hash}`
- `act:rp_assign:{conversation_id}:{team_or_assignee}:{customer_message_id or hash}`
- `act:shopify_lookup:{conversation_id}:{order_id}` (optional, mainly for caching)

> Important: idempotency keys should be derived from **immutable** event properties.
> Do not use values that can change (like “current tags list”).

#### A.2 Write patterns (DynamoDB conditional writes)
Worker stage:
- `PutItem(event_id=<canonical_id>)` with condition: `attribute_not_exists(event_id)`
  - if succeeds → first time seen → proceed
  - if fails → already processed/processing → short-circuit safely

---

### Table B — `rp_mw_conversation_state` (recommended; now provisioned)
Purpose:
- maintain minimal state needed for multi-step flows and safe throttling
- prevent repeated auto-replies (e.g., do not send “order status” response 5 times)

**Primary key**
- Partition key: `conversation_id` (string)

**Required attributes**
- `updated_at` (ISO timestamp)
- `expires_at` (epoch seconds) — TTL attribute

**Recommended attributes (v1)**
- `last_processed_at` (ISO timestamp)
- `last_processed_message_id` (string, optional)
- `last_routed_team` (string, optional)
- `last_routing_confidence` (number, optional)
- `last_intent` (string, optional)
- `risk_flags` (string set, optional) — e.g., `{"chargeback","fraud_suspected"}`
- `pending_flow` (object, optional)
  - example: `{ "type": "need_order_number", "requested_at": "<ISO_TIMESTAMP>", "attempts": 1 }`
- `last_auto_reply` (object, optional)
  - example: `{ "type": "order_status", "sent_at": "<ISO_TIMESTAMP>", "source_message_id": "<MESSAGE_ID>" }`

**Recommended TTL**
- 90 days for general conversation state (configured as `expires_at` TTL in CDK)
- For `pending_flow` content that includes sensitive identifiers (e.g., order number):
  - store only if necessary
  - store minimal (last-4 or hashed)
  - consider a shorter TTL (7–30 days)

#### B.1 Concurrency model (important)
We aim to process messages for a given conversation **sequentially** via:
- SQS FIFO `MessageGroupId = conversation_id`

This reduces or eliminates the need for distributed locks.

However, we still recommend storing a `version` integer for optimistic concurrency if we ever:
- change queue type, or
- add parallel processing per conversation, or
- introduce secondary workers.

---

### Table C — `rp_mw_audit_actions` (lightweight audit; provisioned)

Purpose:
- lightweight audit trail of what the middleware did (without storing raw text)
- helpful for incident response and “why was this routed here?”

**Primary key**
- Partition key: `conversation_id` (string)
- Sort key: `ts_action_id` (string, e.g., `{timestamp}#{action_id}`)

**Attributes**
- `action_type` (e.g., `route`, `tag`, `auto_reply`, `escalate`)
- `action_payload_redacted` (small JSON string; no PII)
- `idempotency_key` (string)
- `result` (success/fail + reason)

**TTL**
- 60 days by default (TTL attribute `expires_at`; adjustable per environment)

> v2 option: If we need durable audit for compliance/process reasons, extend retention or export to an encrypted store with stricter access controls.

---

## 2) Data retention and minimization rules (v1)

### 2.1 Do not store raw message bodies by default
- Store `payload_hash` (sha256) and **maybe** a redacted excerpt (first ~80 chars) only if required for debugging.
- Any excerpt MUST be redacted (emails/phones/order #/tracking).

### 2.2 Redaction standards (minimum)
Mask:
- email addresses → `***@***`
- phone numbers → `***-***-1234`
- order numbers → `***1234`
- tracking numbers/links → `***`

(Full rules live in: `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`.)

---

## 3) How this fits the processing pipeline

1) Ingress Lambda:
   - normalize payload
   - compute `event_idempotency_key`
   - enqueue to SQS FIFO (no DynamoDB writes at ingress; storage happens in worker)
   - ACK 200 fast

2) Worker Lambda:
   - load kill switches (safe_mode + automation_enabled)
   - write idempotency record (Table A, conditional put)
   - emit state (Table B) + audit (Table C) with TTL
   - (future) compute decision (route / FAQ assist / verified auto-reply) and action idempotency keys
   - on 429/timeouts → retry policy (see `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`)

---

## 4) Open design choices (tracked, not blocking)
- ✅ v1 audit table provisioned (Table C) with TTL; usage optional per environment.
- Whether to implement a distributed rate limiter using DynamoDB (likely unnecessary at current volumes).
- Whether to add an encrypted S3 replay archive (useful, but increases governance burden).