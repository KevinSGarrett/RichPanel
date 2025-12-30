# Rate Limiting and Backpressure

Last updated: 2025-12-21
Last verified: 2025-12-21 — Expanded v1 rate-limit strategy (Richpanel/OpenAI/Shopify).

This document defines how we prevent:
- 429 storms
- slowdowns/backlogs during spikes
- partial “write failures” (route applied but reply not sent, etc.)
- cascading failures across downstream dependencies

Primary downstreams:
- Richpanel API (routing tags, assignments, replies, order lookup)
- OpenAI API (classification + automation replies)
- Shopify Admin API (optional fallback for order status/tracking)

Related docs:
- Common issues: `CommonIssues.zip/05-rate-limits.md`
- Idempotency & retries: `docs/03_Richpanel_Integration/Idempotency_Retry_Dedup.md`
- Failure modes: `docs/07_Reliability_Scaling/Failure_Modes_and_Recovery.md`

---

## 0) Core principles (v1)

### 0.1 Reduce calls before throttling
The cheapest rate-limit is the one you never trigger.
We prefer:
- include needed context in the Richpanel HTTP Target payload
- cache stable metadata (team IDs, tag IDs)
- minimize update calls (set tags/assignment in one write if possible)

### 0.2 Queue everything (ACK fast)
Ingress is ACK-fast and enqueues work.
All “slow” work happens asynchronously.

### 0.3 Concurrency caps are our first safety rail
At current volumes, a simple and robust strategy is:
- cap worker concurrency (Lambda reserved concurrency)
- process sequentially per conversation (SQS FIFO MessageGroupId)

This alone often prevents most 429 issues without needing complex distributed limiters.

### 0.4 Honor 429 responses correctly
When downstream returns 429:
- respect `Retry-After` when present
- exponential backoff + jitter
- do not hammer

---

## 1) Rate-limit budget model (v1)

We model downstream capacity in “requests per second” and “requests per message”.

### 1.1 Downstream budgets we must respect
**Richpanel** (from common issues reference): ~50 requests / 30 seconds (≈ 1.67 rps sustained).
OpenAI + Shopify: vary by account; treat as unknown until confirmed.

### 1.2 Our default safe allocations
Because we don’t yet know OpenAI/Shopify quotas, v1 uses conservative concurrency:

- Worker Lambda reserved concurrency: **5** (tunable)
- Ingress Lambda reserved concurrency: **unbounded** (it only enqueues + returns fast)

We also enforce “per-worker request spacing” to Richpanel writes when needed.

---

## 2) Implementation strategy (layered)

### Layer 1 — Concurrency caps (required)
- SQS queue → Lambda trigger with reserved concurrency
- SQS FIFO groups by `conversation_id` to avoid conversation-level races

**Why it works well early:**
- bursts are smoothed by the queue
- global parallelism is bounded
- fewer downstream calls happen at once

### Layer 2 — Per-downstream token buckets (recommended)
Inside the Worker Lambda:
- maintain token buckets per downstream:
  - `richpanel_read`
  - `richpanel_write`
  - `openai`
  - `shopify_read`

**v1 implementation option (simple):**
- in-memory token bucket per Lambda container instance
- combined with low reserved concurrency, this is usually sufficient

**v2 option (scales better):**
- distributed limiter via DynamoDB atomic counters (more cost/complexity)

### Layer 3 — Retry queues (recommended)
For retryable failures, avoid immediate hot-loop retries.

Recommended pattern:
- Main queue: `rp-mw-events.fifo`
- Retry queue(s): `rp-mw-retry-60s`, `rp-mw-retry-10m`
- DLQ: `rp-mw-dlq`

Worker behavior:
- if retryable error:
  - publish to retry queue with metadata (attempt count, last error)
  - ack/delete original message
- if max attempts exceeded:
  - publish to DLQ
  - tag conversation in Richpanel (if safe/possible) e.g., `middleware_error_needs_attention`

> If we keep v1 simpler, we can rely on SQS redrive alone.
> The tradeoff is less control over retry timing/backoff.

---

## 3) 429 handling policy (must be consistent)

### 3.1 What counts as retryable
Retryable:
- 429
- 5xx
- timeouts / connection errors

Non-retryable (treat as configuration bug):
- 401/403 (bad key/permissions)
- 400/422 (bad payload / invalid request)
- 404 (wrong IDs)

### 3.2 Backoff schedule (v1 recommended)
- attempt 1: delay 2–5s (jitter)
- attempt 2: delay 10–20s
- attempt 3: delay 60–120s
- attempt 4+: move to retry queue (10m) or DLQ

Always:
- prefer `Retry-After` if provided

---

## 4) Backpressure signals & protective actions

### 4.1 Signals
- queue depth growing
- worker max concurrency saturated
- 429 rate trending up
- median processing latency increasing

### 4.2 Protective actions (in priority order)
1) **Stop auto-replies** (kill switch) but keep routing (if safe)
2) Switch to “route-only” mode for all but highest confidence FAQ
3) Disable Shopify fallback lookups (if they are the bottleneck) and ask for order #
4) Reduce classification complexity (shorter prompts / smaller model)

---

## 5) LiveChat “real-time lane” (optional; **deferred in v1**)
Since LiveChat is the only real-time channel in v1, we considered a separate queue lane, but:

Optional improvement:
- v2 option: separate queue: `rp-mw-livechat.fifo`
- higher reserved concurrency for that queue
- same idempotency tables

In v1 we will **not** add a separate lane; we will instead cap concurrency and monitor LiveChat p95. If needed, we can add a separate lane later.

We will only implement this if we observe:
- LiveChat p95 latency > 15–25s
- queue backlog consistently delays LiveChat

---

## 6) Common pitfalls (explicitly avoided)
- Doing OpenAI/Shopify calls in the webhook request thread (violates ACK-fast)
- Assuming Richpanel will retry HTTP Target delivery reliably
- Retrying immediately in a tight loop on 429 (causes cascade)
- Multiple Richpanel write calls per message when one would do

