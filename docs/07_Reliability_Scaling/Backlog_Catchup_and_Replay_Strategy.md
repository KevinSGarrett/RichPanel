# Backlog Catch-up and Replay Strategy (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 07)**

This document defines how we safely catch up when messages accumulate in the queue (SQS backlog) and how we replay DLQ items without causing:
- rate-limit storms
- duplicate replies / duplicate routing
- runaway cost
- prolonged customer delays

Related:
- Idempotency schema: `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
- Tuning playbook: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

---

## 1) Definitions
- **Backlog**: SQS has a non-trivial number of visible messages and/or oldest message age is above target.
- **Catch-up**: increasing drain rate until backlog returns to normal.
- **Replay**: reprocessing messages from DLQ or manually re-enqueued messages.

---

## 2) Safety principles
1) **Idempotency first**: every event and every action (reply, add-tag, assign) must be idempotent.
2) **Prefer route-only during recovery**: customer-facing automation is disabled when the system is unstable.
3) **Drain gradually**: backlog recovery is controlled by concurrency caps, not “as fast as possible.”
4) **Honor vendor limits**: Richpanel 429 and OpenAI errors should *reduce* concurrency, not trigger retries storms.

---

## 3) Backlog catch-up procedure

### Step 0 — Stabilize
If backlog is caused by vendor instability or errors:
- Set `safe_mode=true`
- If costs are spiking, also set `automation_enabled=false`

### Step 1 — Determine backlog severity
Use:
- SQS oldest message age
- SQS visible messages
- Worker error rate
- Vendor 429/error rates

Severity guide:
- **Mild**: queue age 60–120s
- **Moderate**: queue age 120–300s
- **Severe**: queue age > 300s or DLQ growth

### Step 2 — Adjust concurrency safely
- Increase worker reserved concurrency in steps of **+2**, waiting 10 minutes between changes.
- Stop increasing if:
  - Richpanel 429 spikes
  - OpenAI errors spike
  - DLQ grows

### Step 3 — Return to steady state
When:
- queue age < 60s for 15 minutes
- error rates are normal

Then:
- return concurrency to baseline (from `parameter_defaults_v1.yaml`)
- exit safe mode only after stability confirmed

---

## 4) DLQ replay strategy

### Why items go to DLQ
Common categories:
- auth/token failures
- malformed payload / schema validation failure
- vendor permanent errors (4xx)
- max retries exhausted (429/5xx/timeouts)

### Replay prerequisites
Before replaying:
- root cause fixed
- idempotency keys remain valid (or replay will be no-op)
- safe mode enabled (recommended)

### Controlled replay options
**Option A: Manual replay (small volume)**
- export DLQ messages
- replay through a controlled script / tool at low rate
- monitor 429s/errors

**Option B: Redrive DLQ to source queue (AWS redrive)**
- only after verifying the bug/auth issue is fixed
- throttle worker concurrency to a safe level

### Replay throttling
- start with worker reserved concurrency at baseline
- increase only if vendor limits allow

---

## 5) Post-recovery validation
After backlog recovery or replay:
- confirm no double replies (audit via idempotency table / tags)
- confirm Tier 0 intents were never auto-responded
- confirm no PII leaked in logs
- document incident + changes

---

## 6) What we do NOT do in v1
- No “unbounded drain” (setting concurrency very high)
- No automated replay without operator review
- No customer-facing automation during unstable vendor conditions
