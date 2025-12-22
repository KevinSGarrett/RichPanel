# Capacity Plan and SLOs

Last updated: 2025-12-21
Last verified: 2025-12-21 — Updated with full 7-day totals and daily ranges.

Inputs:
- `Agent Activity Heatmap.csv` (7-day hourly volume)
- `SC_Data_ai_ready_package.zip` (conversation types distribution; planning only)

---

## 1) Current volume snapshot (from provided heatmap)

From `Agent Activity Heatmap.csv` (168 hourly rows = 7 days):
- Total inbound messages (7 days): **35,465**
- Avg per day: **~5,066**
- Min day: **~3,928 (Sat)**
- Max day: **~5,658 (Mon)**
- Avg per hour: **~211**
- Peak hour: **430 messages/hour** (Sun 02:00 PM)

Directional scaling thought experiment:
- 2× peak ≈ 860/hour
- 5× peak ≈ 2,150/hour
- 10× peak ≈ 4,300/hour (~72/minute, ~1.2/sec)

Even 10× peak remains a good fit for a queue-based serverless architecture.

> Note: These numbers assume “Messages Received” ≈ inbound customer messages.
> If this metric includes other traffic, we will recalibrate after we confirm Richpanel event payload semantics.

---

## 2) Channel mix (from SC_Data — directional)
In the provided SC_Data sample, the dominant conversation types are:
- `email`
- `email_from_widget`
- `tiktok_shop_message`
- `facebook_feed_comment`

Implication:
- most volume is not ultra-real-time chat
- we can use relaxed processing latency SLOs for email-like channels,
  while keeping tighter SLOs for LiveChat (v1 real-time channel)

---

## 3) Recommended SLOs (early rollout defaults)

### 3.1 Webhook/trigger acknowledgement (ingress)
**Goal:** never block Richpanel waiting on OpenAI/Shopify.

- **Ack latency (p95):** < 500 ms
- **Ack latency (p99):** < 1.5 s
- **Ack success rate:** 99.9%+

### 3.2 Processing latency (route/auto-reply)

#### Real-time lane (LiveChat only, v1)
- **Routing applied p95:** < 15 s
- **Verified auto-reply p95 (if applicable):** < 25 s
- **p99:** < 60 s

#### Async lane (email/social/TikTok)
- **Routing applied p95:** < 60 s
- **Verified auto-reply p95 (if applicable):** < 120 s
- **p99 degraded mode:** < 10 min

### 3.3 Backlog SLO (queue age)
- **SQS oldest message age (p95):** < 60 s
- Alert when:
  - age > 2 min for 5+ minutes (warning)
  - age > 10 min (critical)

---

## 4) Capacity controls (must-have)

### 4.1 Concurrency caps
To protect downstream rate limits:
- Worker Lambda uses **reserved concurrency** (v1 start: 5).
- Prefer SQS FIFO group-by conversation_id to reduce race conditions.

### 4.2 Backpressure + rate-limit handling
See:
- `Rate_Limiting_and_Backpressure.md`

