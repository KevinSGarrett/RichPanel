# Load Testing and Soak Test Plan

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

This is a **documentation plan** for load testing the middleware before production rollout.
It is intentionally tool-agnostic; Cursor builders can implement using k6 / Artillery / Locust.

Inputs for sizing:
- Observed peak: 430/hour (~0.119 msg/sec)
- Planned surge factor: 10× peak (~4,300/hour)

---

## 1) What we are testing (scope)

We test:
- Ingress endpoint durability (ACK-fast)
- Queue buffering correctness (no loss, bounded backlog)
- Worker processing throughput and latency SLOs
- Idempotency behavior under duplicates/retries
- Degraded mode behavior under 429 / vendor outages
- Cost guardrails (token usage does not explode)

We do **not** test agent productivity or UI workflows here (Wave 10).

---

## 2) Test environments
- **Staging** must be production-like:
  - same architecture (API Gateway → SQS FIFO → Lambda → DynamoDB)
  - separate vendor keys (OpenAI/Richpanel/Shopify)
  - safe channels or test tenant to avoid messaging real customers

---

## 3) Test datasets
Use synthetic inputs derived from:
- high-frequency intents (order status, returns, troubleshooting)
- Tier 0 intents (chargeback/dispute, threats, fraud)
- multi-intent messages
- messages containing tricky JSON characters (quotes/newlines/emoji)

All test payloads must be **PII-scrubbed** or synthetic.

---

## 4) Load profiles

### 4.1 Baseline profile (expected traffic)
- steady rate: mean hour rate (~211/hour)
- duration: 60 minutes
- goal: confirm no errors, stable latencies, low queue age

### 4.2 Peak profile (observed peak hour)
- steady rate: 430/hour
- duration: 60 minutes
- goals:
  - meet routing SLOs
  - no meaningful 429 spikes
  - no duplicate replies

### 4.3 Surge profile (10× peak)
- steady rate: 4,300/hour
- duration: 15 minutes
- goals:
  - queue buffers load without dropping
  - queue age increases but remains bounded and recovers within 30–60 minutes
  - degrade modes trigger correctly if needed (disable auto-replies)

### 4.4 Spike profile (burst)
- burst: 1,000 messages in 60 seconds (or equivalent)
- goals:
  - ingress stays healthy
  - SQS absorbs burst
  - worker processes backlog without duplicates

### 4.5 Soak test (stability)
- steady rate: ~p50 hour rate (~224/hour)
- duration: 24 hours
- goals:
  - no memory leaks or unbounded log growth
  - stable token usage per message
  - stable queue age

---

## 5) Failure-injection tests (must-have)

### 5.1 OpenAI degraded
Simulate:
- timeouts
- 5xx errors
Expected:
- route-only fallback
- no auto-replies
- backlog remains bounded

### 5.2 Richpanel rate limited (429)
Simulate:
- 429 with Retry-After
Expected:
- backoff honored
- concurrency reduced
- queue backlog grows but recovers
- no infinite retries

### 5.3 Shopify unavailable (if enabled)
Expected:
- no tracking disclosures without deterministic match
- ask for order # and route

---

## 6) Pass/fail criteria (v1)

Hard fail:
- any unsafe auto-reply (Tier 0 should never auto-send)
- duplicate auto-replies for same customer message
- idempotency violations
- queue backlog does not recover after surge ends

Soft fail / tuning needed:
- routing latency p95 above SLO (but no unsafe behavior)
- sustained 429s above threshold
- cost per message exceeds guardrail targets

---

## 7) Required outputs (artifacts)
Each test run must produce:
- load configuration (rate, duration, payload mix)
- latency percentiles (ACK and end-to-end)
- queue age trend
- 429 counts per downstream
- error rate by class
- duplicates detected (idempotency)
- cost proxy metrics (OpenAI tokens/message; Lambda duration/message)

These artifacts become baselines for Wave 09 release gates.
