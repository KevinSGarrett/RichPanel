# Load and Soak Testing

Last updated: 2025-12-22  
Scope: Wave 09 (testing) + Wave 07 (capacity) alignment.

This document defines **how we prove** the middleware can handle:
- real traffic patterns (from your Agent Activity Heatmap)
- spikes, bursts, and backlog catch-up
- vendor rate limits (Richpanel / OpenAI / Shopify)
- safe degradation (route-only / safe-mode)

---

## Guiding principles
- **Measure end-to-end latency via logs/metrics**, not only client-side response time.
- **ACK fast** is the main contract with Richpanel; everything else is async.
- Load testing must include **rate-limit and partial failure simulation**, not only “happy-path throughput”.

---

## Traffic baseline (from your heatmap)
We size tests from:
- typical hourly volumes
- peak hour
- “worst plausible” burst behavior

Wave 07 already recorded:
- 7-day total: 35,465 messages
- average/day: ~5,066
- peak hour: 430 messages (Sun 02:00 PM)

We translate this into scenarios rather than a single RPS number.

---

## Success criteria (minimum)

### Ingress / ACK
- p95 ACK < 500ms
- p99 ACK < 1.5s
- error rate < 0.1% (5xx)

### Queue + worker
- backlog (oldest message age) returns to near-zero after spike within agreed recovery window
- no runaway retries; DLQ receives only true poison cases
- safe-mode triggers work (automation can be disabled without breaking routing)

### Vendor safety
- during simulated 429 storms, system **backs off** and continues draining safely
- no double replies / double tag applications (idempotency holds)

### Cost guardrails
- token usage per message stays within expected bounds
- no “accidental fan-out” (e.g., 5 OpenAI calls per message) without explicit approval

---

## Load test scenarios (v1)

### Scenario A — Peak hour replay (baseline)
- Simulate 430 messages distributed over 60 minutes (steady state).
- Verify:
  - stable queue depth
  - no sustained throttling
  - correct routing ratio distribution

### Scenario B — 5× spike (still realistic)
- Simulate 2,150 messages over 60 minutes.
- Verify:
  - queue grows but remains controlled
  - worker concurrency caps prevent vendor storm
  - backlog drains within defined window

### Scenario C — Burst (worst-case webhook burst)
- Simulate 100 messages in 2 minutes (burst), repeated 3 times.
- Verify:
  - ingress remains healthy (ACK fast)
  - queue absorbs burst
  - worker throttling prevents vendor overload

### Scenario D — Vendor 429 storm (Richpanel)
- Use stubbed Richpanel API that returns:
  - 429 with `Retry-After` intermittently
- Verify:
  - worker respects `Retry-After`
  - no hot-loop retries
  - DLQ does not fill with rate-limit errors (rate limits should be retryable)

### Scenario E — OpenAI latency degradation
- Simulate OpenAI p95 latency +3× and some 5xx.
- Verify:
  - timeouts occur in a controlled way
  - policy engine fail-closed route-only is used
  - backlog grows but drains

### Scenario F — Backlog catch-up (replay)
- Inject 10k messages into the queue (simulate downtime).
- Bring workers online and measure drain behavior.
- Verify:
  - catch-up uses controlled concurrency
  - no vendor storm
  - cost guardrails remain in place

---

## Test harness recommendation
We recommend a two-layer harness:

1) **Ingress load generator**
   - tool: k6 / Artillery / Locust (any is fine)
   - hits API Gateway endpoint with minimal payload (`ticket_id`, `event_type`, etc.)

2) **Downstream stubs**
   - Richpanel stub server:
     - supports 200/429/500 scripted behavior
   - OpenAI stub:
     - returns valid/invalid schema outputs, latency injection
   - Shopify stub (optional)
   - Goal: reproduce vendor behavior deterministically

We do **not** need real vendor calls for load tests; the goal is middleware resilience.

---

## Observability requirements (must-have for load tests)
A load test run is not “complete” unless we capture:
- ack latency distribution
- worker processing latency distribution
- queue age + depth over time
- retry counts and DLQ counts
- vendor 429/5xx rates
- “automation disabled/safe-mode entered” events

See: `docs/08_Observability_Analytics/Metrics_Catalog_and_SLO_Instrumentation.md`.

---

## How this connects to Wave 07
Wave 07 defines:
- parameter defaults
- degraded mode playbook
- backlog drain strategy

This Wave 09 doc ensures we **test those behaviors**.

Key references:
- `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
- `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
