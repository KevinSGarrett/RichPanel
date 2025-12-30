# Concurrency and Throughput Model

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

Purpose:
- translate observed inbound volume into safe **Lambda concurrency**, **SQS configuration**, and **downstream request budgets**
- ensure we meet SLOs without triggering 429 storms or runaway costs

Related:
- `Capacity_Plan_and_SLOs.md`
- `Rate_Limiting_and_Backpressure.md`
- `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
- Wave 06 kill switch: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

---

## 1) Observed inbound rates (from heatmap)

Peak hour: **430/hour** ≈ **0.119 msg/sec**  
P95 hour: **362.6/hour** ≈ **0.101 msg/sec**

This is relatively modest volume; reliability risks are dominated by:
- downstream rate limits
- duplicate deliveries / loops
- partial writes (route applied but reply failed)
- outages (OpenAI/Richpanel) causing backlog

---

## 2) Work-per-message model

Each inbound customer message can cause **some subset** of the following actions.

### 2.1 “Read” actions
- (optional) fetch ticket details from Richpanel
- (optional) fetch linked order ID from Richpanel (`/v1/order/{conversationId}`)
- (optional) fetch full order details

### 2.2 “Compute” actions
- 1× LLM classification call (structured output)
- (optional) Tier 2 verifier call (only when candidate automation needs deterministic match)

### 2.3 “Write” actions
- apply routing tags
- assign to a team/queue (depending on routing mechanism)
- (optional) send an auto-reply (template-based; no LLM generation)

**Important:** the *rate limiting bottleneck* is typically **writes** to Richpanel, not compute.

---

## 3) Concurrency sizing (Little’s Law)

`Concurrency_needed ≈ Arrival_rate * Avg_processing_time_seconds`

Example (peak):
- Arrival_rate ≈ 0.119 msg/sec
- If Avg_processing_time = 5 sec → Concurrency ≈ 0.60

Even with 10× peak and 10 sec processing time, concurrency remains manageable.

### 3.1 What actually limits us: downstream request budget
If Richpanel quota is roughly ~1.67 requests/sec sustained (50 requests / 30 sec), then:

`Max_msg_rate ≈ Richpanel_rps_budget / Richpanel_calls_per_message`

Illustrative examples:
- 2 calls/message → ~0.83 msg/sec (~3,000/hr)
- 4 calls/message → ~0.42 msg/sec (~1,500/hr)

Our observed peak is ~0.119 msg/sec (~430/hr), which is well below these bounds.

**Conclusion:** concurrency can remain low and still meet SLOs.

---

## 4) Recommended v1 settings (best-suggested defaults)

### 4.1 Worker Lambda reserved concurrency
Start: **5**  
Why:
- enough to clear backlog quickly at current volumes
- small enough that a bug doesn’t stampede downstreams

Tuning rules:
- if queue age grows but 429s are low → increase gradually (5 → 10 → 15)
- if 429s rise → reduce concurrency and/or enable stronger throttling

### 4.2 Per-downstream throttling
Even with low concurrency, implement per-downstream pacing:
- token bucket or fixed spacing for Richpanel writes
- honor `Retry-After` headers
- jittered exponential backoff

(Implementation details documented in `Rate_Limiting_and_Backpressure.md`.)

### 4.3 SQS configuration
If using FIFO:
- `MessageGroupId = conversation_id` (preserves per-conversation ordering)
- `MessageDeduplicationId = message_id` (if available) else hash(payload)

Recommended operational values:
- Visibility timeout: 2–5× p99 worker time (start: 60–120s, adjust after measurement)
- Redrive to DLQ after: 3–5 receives (start: 5)

### 4.4 Timeouts (hard limits)
To prevent stuck workers and infinite backlog growth:
- OpenAI call timeout: 10–20s (hard cap)
- Richpanel calls: 5–10s each
- Worker total timeout: 30–60s (depends on order lookup paths)

---

## 5) “Degraded mode” throughput policy

When any of these are true:
- queue age > 2 minutes (warning)
- Richpanel 429 rate rising
- OpenAI latency spikes

Automatically shift to **degraded mode**:
1) Disable auto-replies (routing only)
2) Skip optional order lookups
3) Route to human triage queues with tags

Kill switch and safe mode are already specified in Wave 06.

---

## 6) What we verify during load testing (Wave 07)
- do we meet SLOs at peak and 10× peak?
- does queue age stay bounded?
- do we avoid 429 storms by design?
- does idempotency prevent duplicate replies?

(See `Load_Testing_and_Soak_Test_Plan.md`.)
