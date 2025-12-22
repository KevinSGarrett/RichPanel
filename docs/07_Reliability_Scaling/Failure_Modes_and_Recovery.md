# Failure Modes and Recovery (Runbook Skeleton)

Last updated: 2025-12-21
Last verified: 2025-12-21 — Added v1 failure catalog + recovery actions.

This document lists likely failure modes for the middleware and how we detect and recover.
It is intentionally practical: “what breaks”, “how to know”, “what to do”.

Related docs:
- Rate limiting: `Rate_Limiting_and_Backpressure.md`
- Idempotency: `docs/03_Richpanel_Integration/Idempotency_Retry_Dedup.md`
- Common issues: `CommonIssues.zip` (especially #1, #3, #4, #5, #12)

---

## 1) High-probability failure modes (v1)

### 1.1 Webhook delivery failures (ingress endpoint down / non-200)
**Symptoms**
- inbound events stop flowing
- sudden drop to near-zero message processing
- Richpanel automations appear “broken”

**Detection**
- API Gateway 5xx/4xx spikes
- ingress Lambda errors
- queue receives drop to zero while Richpanel traffic continues

**Recovery**
- roll back last deploy (if correlated)
- verify API Gateway stage + Lambda integration health
- verify Richpanel HTTP Target URL + auth config
- confirm DNS/SSL if applicable
- if needed, temporarily route all tickets to human teams until recovered

**Prevention**
- ACK-fast design
- health checks + alarms
- “assume Richpanel will not retry” (internal durability)

---

### 1.2 Duplicate events / double actions
**Symptoms**
- customers receive duplicate replies
- tags appear twice / loops
- conversations bounce between teams

**Detection**
- metric: `idempotency_duplicates_detected`
- metric: `auto_reply_sent` spikes without matching inbound volume
- support reports “duplicate messages”

**Recovery**
- enable kill switch for auto-replies immediately
- verify idempotency keys
- verify “middleware_processed” tag/loop-prevention logic
- replay a small sample through staging

**Prevention**
- DynamoDB idempotency conditional writes
- action-level idempotency

---

### 1.3 Downstream rate limit (429) or throttling
**Symptoms**
- delays in routing / tagging
- partial updates (route computed but not applied)
- rising queue backlog

**Detection**
- 429 rate metric per downstream
- increased worker duration / retries
- queue depth growth

**Recovery**
- reduce worker concurrency
- disable non-essential calls (Shopify fallback, optional data fetch)
- switch to “route-only” mode (no auto-replies)
- honor Retry-After; avoid hot-loop retries

**Prevention**
- concurrency caps
- token bucket limiter
- retry queues + jitter

---

### 1.4 OpenAI outage / high latency
**Symptoms**
- classification fails or times out
- workers retry and backlog grows

**Detection**
- OpenAI error rate
- classification latency metric
- timeout count

**Recovery**
- switch to fallback routing:
  - if high-signal keyword rules exist → use them
  - else route to a safe default team (e.g., LiveChat Support / Email Support) with tag `needs_manual_triage`
- disable auto-replies (kill switch)

**Prevention**
- strict timeouts
- route-only fallback path
- shadow-mode eval before expanding automation

---

### 1.5 Partial side effects (routing applied but reply failed, or vice versa)
**Symptoms**
- conversation tagged/assigned but customer didn’t receive expected info
- customer repeats question

**Detection**
- action audit logs show partial execution
- mismatch metrics: `decisions_made` vs `actions_success`

**Recovery**
- idempotent re-run of action with action idempotency key
- avoid re-sending customer reply if already sent

**Prevention**
- record action idempotency keys for each step
- execute steps in safe order (e.g., record action before calling downstream when feasible)

---

## 2) Global safety controls (must-have)
- **Kill switch**: disable auto-replies immediately
- **Shadow mode**: log-only mode for tuning
- **DLQ**: capture poison messages for later inspection
- **Alerting**:
  - queue depth
  - 429 rate
  - worker error rate
  - latency p95/p99
  - idempotency duplicate rate

---

## 3) Incident severity levels (draft)
- SEV0: customers receiving wrong/unsafe replies at scale → kill switch immediately
- SEV1: routing broken or massive backlog → reduce concurrency, triage
- SEV2: partial degradation (slower routing) → monitor + tune

(Full incident response lives in Wave 10.)

