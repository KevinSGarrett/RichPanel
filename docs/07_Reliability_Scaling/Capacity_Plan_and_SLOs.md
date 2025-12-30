# Capacity Plan and SLOs

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

Inputs:
- `Agent Activity Heatmap.csv` (7-day hourly volume)
- `SC_Data_ai_ready_package.zip` (conversation examples; planning + eval)
- Wave 04/05 policy gates (Tiering, deterministic-match constraints)

---

## 1) Current volume snapshot (from provided heatmap)

**7-day total inbound messages:** **35,465**  
**Average per day:** **5066**  
**Average per hour:** **211.1**  
**Peak hour:** **430 messages/hour** (Sun 02:00 PM)

### 1.1 Daily totals (messages received)
| Day | Messages Received |
|---|---:|
| Sun | 5,342 |
| Mon | 5,658 |
| Tue | 5,527 |
| Wed | 5,167 |
| Thu | 4,908 |
| Fri | 4,935 |
| Sat | 3,928 |

### 1.2 Hourly distribution (messages/hour)
| Metric | Messages/hour |
|---|---:|
| Mean | 211.1 |
| P50 | 223.5 |
| P90 | 327.3 |
| P95 | 362.6 |
| P99 | 423.0 |
| Max | 430 (Sun 02:00 PM) |

### 1.3 Data quality notes (do not ignore)
A few hours show **high “Messages Received” but near-zero “Unique Conversations Messaged”**, e.g.:
- Wed 03:00 AM — 324 received, 0 unique conv
- Fri 03:00 AM — 307 received, 0 unique conv
- Sat 03:00 AM — 379 received, 1 unique conv

This might indicate one or more of:
- non-customer traffic included in “Messages Received”
- reporting mismatch overnight
- “Unique Conversations Messaged” measures agent outbound, not inbound

**Capacity planning default:** treat `Messages Received` as the *upper bound* for inbound message events, and apply a safety factor for spikes.

---

## 2) Reliability objectives (SLOs)

### 2.1 Ingress acknowledgement (webhook/HTTP Target)
Goal: Richpanel should never wait on OpenAI/Shopify.

- **ACK latency p95:** < 500 ms
- **ACK latency p99:** < 1.5 s
- **ACK success rate:** 99.9%+

### 2.2 Processing latency (route + optional auto-reply)

#### Real-time class (LiveChat only, v1)
- **Routing applied p95:** < 15 s
- **Verified auto-reply sent p95 (if applicable):** < 25 s
- **p99 end-to-end:** < 60 s

#### Async class (email/social/TikTok)
- **Routing applied p95:** < 60 s
- **Verified auto-reply sent p95 (if applicable):** < 120 s
- **p99 degraded mode:** < 10 min

### 2.3 Backlog SLO (queue age)
- **SQS oldest message age p95:** < 60 s

Alerting:
- **Warning:** age > 2 min for 5+ minutes
- **Critical:** age > 10 min

---

## 3) Throughput model (how much worker concurrency we actually need)

We use **Little’s Law** for rough sizing:

`Concurrency_needed ≈ Arrival_rate * Avg_processing_time_seconds`

Where:
- Arrival_rate is in messages/second
- Avg_processing_time_seconds is the worker time including downstream calls (OpenAI + Richpanel + optional order lookup)

### 3.1 Baseline sizing (from observed peak)
Observed peak: 430/hour ≈ 0.119 msg/sec

If avg processing time is:
- 2 seconds → concurrency ≈ 0.24
- 5 seconds → concurrency ≈ 0.60
- 10 seconds → concurrency ≈ 1.19

In other words, **current traffic fits comfortably inside single-digit concurrency**.

### 3.2 Safety factor (campaigns, outages, backlog catch-up)
We plan for:
- **10× peak** (marketing / surge) and
- **backlog catch-up** after a short outage

10× peak: ~4,300/hour ≈ 1.19 msg/sec  
At 5s avg processing time → concurrency ≈ 6.0

This still fits well within serverless limits, but **rate limits** become the true bottleneck (see rate-limit doc).

---

## 4) Capacity controls (must-have)

### 4.1 Queue buffering (required)
Ingress must always enqueue and return quickly.
Worker pulls from queue asynchronously.

### 4.2 Worker concurrency caps (required)
Primary control knob:
- Worker Lambda **reserved concurrency** (start conservative)

**Recommended v1 starting values:**
- worker reserved concurrency: **5**
- adjust based on:
  - Richpanel 429 rate
  - queue age
  - OpenAI latency

### 4.3 Degradation modes (required)
When backlog or 429 rates rise:
1) **Disable auto-replies** (keep routing)
2) Route-only for all intents except the safest Tier 1 templates
3) Disable Shopify fallback (ask order # instead)

Kill switch details live in Wave 06.

---

## 5) Acceptance criteria (Wave 07)
Wave 07 is considered “complete” when we have:
- a testable throughput model (this doc)
- a load/soak test plan (Wave 07 doc)
- explicit SQS/Lambda/DynamoDB sizing + limits documented
- a clear degradation & recovery playbook (Failure modes doc)
