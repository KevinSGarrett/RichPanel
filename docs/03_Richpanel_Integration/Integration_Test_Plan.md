# Richpanel Integration Test Plan (Wave 03)

Last updated: 2025-12-29
Last verified: 2025-12-29 — Created initial integration test matrix for HTTP Target + routing tags + safe auto-replies.

This plan defines how we validate Richpanel ↔ middleware integration before enabling production routing/automation.

---

## 0) Test environments
### 0.1 Recommended environments
- **Dev**: isolated account + Richpanel API key (may share a single Richpanel workspace if you can separate via routing tags)
- **Staging**: preferred: separate Richpanel workspace/brand if available; otherwise use strict tagging to isolate tests
- **Prod**: final validation only; no destructive actions

### 0.2 Test data rules
- Use **test customers** when possible.
- Never paste/store full customer PII in logs or docs.
- For “real sample threads” (SC_Data), use aggregate analysis only.

---

## 1) Pre-flight checklist
- [ ] Richpanel HTTP Target is configured to call the correct environment endpoint.
- [ ] Middleware rejects requests without `X-Middleware-Token`.
- [ ] Middleware ACKs within < 500ms p95 (ingress Lambda).
- [ ] Middleware enqueues to SQS FIFO with MessageGroupId = `conversation_id`.
- [ ] DynamoDB idempotency conditional writes are enabled.

---

## 2) Core functional tests

### 2.1 Inbound-only trigger tests (loop prevention)
**Goal:** Ensure only customer messages trigger middleware.

1) Customer sends message → webhook fires → middleware processes  
   Expected: 1 ingress event, 1 processing job.

2) Agent replies in Richpanel UI  
   Expected: **no** webhook OR middleware drops event (if webhook fires anyway).

3) Middleware sends auto-reply via API  
   Expected: does not re-trigger (or if it triggers, the handler drops due to author-type / `mw-auto-replied` tags / idempotency).

Pass criteria:
- No infinite loops.
- No repeated routing changes after reply.

### 2.2 Routing tag application
**Input:** a test conversation that should go to each team.

Expected:
- middleware applies exactly one `route-*` tag per routing decision
- middleware sets `mw-routing-applied`
- Richpanel assignment rule assigns to the correct Team

Negative cases:
- ambiguous text → route to default queue + `mw-escalated-human`
- low confidence → no route tag; assign to Email Support Team (or your chosen default)

### 2.3 Chargeback/dispute routing (Tier 0)
Test with subject lines and body examples:
- “a chargeback was opened”
- “Chargeback for order …”
- payout/recurring/chargeback notification

Expected:
- route tag `route-chargebacks-disputes`
- **no auto-reply**
- **no auto-close**
- `mw-escalated-human` applied

### 2.4 FAQ automation — order status (Tier 2)
Two scenarios:

A) Deterministic match exists (Richpanel order linked or order# extracted + verified):
- Expected: auto-reply includes tracking link/status (per allowed disclosure)
- Tag: `mw-auto-replied`

B) No deterministic match:
- Expected: Tier 1 “please provide your order number” + route to Email Support Team or Returns Admin depending on intent

### 2.5 Attachments handling
Test cases:
- image attachment (photo)
- multiple attachments burst (5–10)
- non-text only message (image only)
- large message text

Expected:
- HTTP Target payload does **not** include inline base64
- middleware handles missing text safely (route to human; request details)
- no payload-size failures

---

## 3) Reliability + failure injection tests

### 3.1 Duplicate delivery
Replay the same webhook payload (same message_id / event_id) 2–5 times.

Expected:
- only one set of side effects (one route tag, one reply)
- duplicates are dropped via idempotency key

### 3.2 Richpanel API errors
Simulate:
- 429 rate limit
- 5xx
- timeouts

Expected:
- worker retries with backoff + jitter
- on exhaustion, message goes to DLQ + alert

### 3.3 OpenAI errors
Simulate:
- timeout
- invalid JSON response
- 429

Expected:
- fallback: route to human (default queue)
- no auto-reply if confidence low

---

## 4) Observability assertions (must-have)
- [ ] Every ingress event has a correlation id (`request_id` / `event_id`)
- [ ] Every worker job logs:
  - conversation_id
  - action idempotency key(s)
  - chosen route tag + confidence
  - whether auto-replied
- [ ] CloudWatch alarms exist for:
  - ingress non-2xx
  - DLQ > 0
  - worker error rate spikes
  - queue age/backlog

---

## 5) Go/No-Go gates for enabling production routing
Minimum criteria:
- routing accuracy meets the Wave 04 acceptance threshold on evaluation set
- 0 observed automation loops in staging
- idempotency proven under duplicate replay
- chargeback cases auto-close only for whitelisted, deflection-safe templates and never auto-reply
- LiveChat p95 routing < 15s in staging under simulated burst

