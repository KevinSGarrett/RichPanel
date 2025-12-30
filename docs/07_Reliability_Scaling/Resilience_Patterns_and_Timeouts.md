# Resilience Patterns, Timeouts, and Degradation Modes

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

This document defines reliability patterns we use so the middleware remains safe and operable during:
- vendor outages (OpenAI, Richpanel, Shopify)
- rate limiting (429)
- sudden spikes in message volume
- internal bugs causing loops or duplicate actions

---

## 1) Core resilience patterns (v1)

### 1.1 ACK-fast ingestion (non-negotiable)
Ingress must:
- validate/auth request
- normalize payload
- enqueue to SQS
- return 2xx quickly

No OpenAI calls, no Shopify calls, and ideally no Richpanel calls in the request thread.

### 1.2 Idempotency everywhere
- event-level idempotency: prevents double-processing
- action-level idempotency: prevents double replies or duplicate tag writes

Authoritative store: DynamoDB conditional writes.

### 1.3 Fail closed for automation
If anything is uncertain or broken:
- **never** send a potentially wrong automated reply
- default to route-only with a “needs manual triage” tag

This is enforced in Wave 04 policy engine design.

### 1.4 Degradation is a feature
We explicitly support these modes:
- **normal:** routing + safe automation when eligible
- **route-only:** routing but no auto-replies
- **log-only (shadow):** record decisions but make no downstream writes
- **safe mode:** strongest restrictions (Tier 0 always routed, Tier 2 disabled)

Kill switch controls live in Wave 06.

---

## 2) Timeouts (v1 defaults)

Timeouts are the simplest circuit breaker.

### 2.1 OpenAI calls
- hard timeout: 10–20 seconds
- on timeout: treat as “classification unavailable” → route to default triage queue

### 2.2 Richpanel API calls
- per call timeout: 5–10 seconds
- on timeout: retry with jitter; if still failing → route-only fallback and log

### 2.3 Shopify calls (optional fallback)
- per call timeout: 5–10 seconds
- if Shopify is slow/unavailable: ask for order # and route to human

### 2.4 Worker total timeout
- 30–60 seconds (depends on whether order lookups happen)

**Important:** worker timeout must be lower than (or aligned to) SQS visibility timeout to avoid duplicate processing.

---

## 3) Circuit breakers (v1 “lightweight”)

We use simple “circuit breakers”:
- if 429 rate is above threshold for N minutes → reduce concurrency + disable auto-replies
- if OpenAI error rate above threshold → route-only mode automatically
- if Richpanel write failures spike → stop writes and alert (log-only)

Implementation detail:
- alarms + on-call runbook can trigger the kill switch
- optional: automated flag flips (future)

---

## 4) Partial failure handling (most common real-world pain)

Typical scenario:
- tags applied successfully
- reply send fails (timeout/429)

We treat each action as:
- independently idempotent
- independently retryable (bounded)

Rules:
- never re-send a reply if we already sent it (action idempotency key)
- if routing tags were applied but reply failed:
  - leave routing as-is
  - allow agent to respond manually
  - optionally enqueue a “reply retry” if safe and within a short window

---

## 5) Recovery objectives (draft)
These are practical goals, not formal commitments:

- If OpenAI is down: keep routing functioning via default triage + tags
- If Richpanel API is down: decisions are logged; actions may be delayed or manual fallback used
- If SQS backlog grows: system recovers automatically once downstream returns, without duplicates

(Full incident response is Wave 10; this doc is the reliability mechanics.)

