# Data Flow and Storage

Last updated: 2026-01-03
Last verified: 2026-01-03 — RUN_20260103_1640Z (pipeline persistence + audit alignment).

This document defines:
- what data the middleware touches
- what it stores (and for how long)
- what it must avoid storing
- how data flows through the pipeline

Related docs:
- DynamoDB schema: `DynamoDB_State_and_Idempotency_Schema.md`
- PII rules: `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`

---

## 1) Data flow (end-to-end)

1) **Customer → Richpanel**
   - customer sends a message via LiveChat / email / social / TikTok

2) **Richpanel → Middleware (HTTP Target / webhook)**
   - triggers only on inbound customer messages (avoid loops)

3) **Ingress Lambda**
   - validates request (auth/signature if available)
   - normalizes payload into our internal schema and computes an **event idempotency key**
   - enqueues event to SQS FIFO (no DynamoDB writes at ingress; persistence happens in worker)
   - returns **200 OK quickly** (ACK-fast)

4) **Worker Lambda**
   - consumes SQS event
   - loads kill-switch flags (safe_mode + automation_enabled) with a short cache
   - writes idempotency record (Table A) via conditional put
   - emits dry-run state to **conversation_state** (Table B) + **audit_trail** (Table C) with TTL
   - (future) runs classification + side effects (routing/automation) when automation is enabled

5) **Middleware → Richpanel**
   - applies routing tags / assignment
   - posts messages where allowed (automation)
   - records action idempotency keys so side effects aren’t duplicated

6) **Observability**
   - metrics: latency, 429 rate, fallback rate, accuracy eval metrics
   - logs: redacted, structured

---

## 2) Data categories we handle

### 2.1 Inbound message data (from Richpanel)
Possible fields:
- message text (customer content)
- attachments metadata (URLs, sizes)
- customer identifiers (email/phone, not always present)
- conversation_id / ticket_id
- channel info (LiveChat vs email)

### 2.2 Derived data (from middleware)
- intent label(s) + confidence score
- extracted entities (order #, tracking intent, product name, etc.)
- routing decision (department/team)
- automation decision (none / safe-assist / verified reply)
- risk flags (chargeback, fraud-like language, threats, etc.)

### 2.3 Enriched data (from Shopify / Richpanel Order APIs)
- order status
- fulfillment status
- tracking number/link (only disclosed on deterministic match)

---

## 3) What we store (v1 recommended)

### 3.1 DynamoDB — idempotency
We store:
- idempotency keys for inbound events + actions
- processing status + timestamps
- payload hash (not raw text)
- short result summary

TTL:
- ~30 days (`expires_at` TTL enabled in CDK)
- Table name: `rp_mw_<env>_idempotency` (PITR on, retain on delete)

### 3.2 DynamoDB — conversation state (minimal)
We store only what we need to:
- avoid repeated auto replies
- support safe multi-step flows (ask for order #)
- maintain last routing decision

TTL:
- ~90 days (tunable; `expires_at` TTL enabled in CDK)
- sensitive pending-flow fields should have shorter TTL or be hashed/redacted
- Table name: `rp_mw_<env>_conversation_state` (PITR on, retain on delete)

### 3.3 Optional durable audit (Table C)
Provisioned as `rp_mw_<env>_audit_trail` with TTL attribute `expires_at` (default 60 days).  
Use for:
- action audit records with redacted payloads
- troubleshooting “why was this routed here?”
Usage is optional per environment; extend/export only if compliance requires longer retention.
(Details in `DynamoDB_State_and_Idempotency_Schema.md`.)

---

## 4) What we do NOT store (v1 default)

- raw customer message bodies (beyond the transient queue event payload)
- full emails/phones in logs or DB (redact/mask)
- any payment data / addresses (even if present in messages)
- attachment binary data (images/pdf content) — handled via fetch-on-demand with strict size limits

If we ever add event replay:
- use encrypted S3 with strict retention + access controls
- store redacted or hashed copies

---

## 5) Retention + deletion policy (draft)

- DynamoDB TTL handles automatic expiry.
- Logs retention configured per environment:
  - dev: short (7–14 days)
  - staging: moderate (14–30 days)
  - prod: longer (30–90 days) as needed for ops

---

## 6) Production safety defaults (v1)
- A kill switch can disable auto replies instantly.
- If order identity cannot be verified: do not disclose order/tracking details.
- If OpenAI fails: route to human with safe fallback tags.

