# Architecture Overview

Last updated: 2025-12-21

This document describes the **recommended production architecture** for the Richpanel routing + FAQ middleware.

---

## 1) High-level reference architecture (recommended)

```
Richpanel (inbound msg)
        |
        |  (HTTP Target / Webhook)
        v
API Gateway  (public endpoint)
        |
        v
Lambda: Ingress / Ack
  - verify request (auth token / allowlist)
  - normalize payload (conversation_id, message_id, channel, text)
  - idempotency pre-check (fast path)
  - enqueue to SQS
  - return 2xx quickly
        |
        v
SQS FIFO Queue (buffer + ordering by conversation_id)
        |
        v
Lambda: Worker / Processor
  - load conversation context/state (DynamoDB)
  - classify: FAQ vs routing vs escalation
  - compute confidence + apply policy thresholds
  - if FAQ: fetch order info (Richpanel Order API and/or Shopify fallback)
  - write actions back to Richpanel (tags, notes, assignments, replies)
  - write audit event + metrics
        |
        +--> OpenAI (routing/intent + entity extraction)
        +--> Richpanel API (tags/notes/messages/assignment)
        +--> Shopify Admin API (fallback order lookup)
        |
        v
DynamoDB (idempotency + state) + CloudWatch (logs/metrics) + DLQ
```

---

## 2) Component responsibilities

### 2.1 Ingress / Ack layer
**Goal:** accept inbound events reliably and return quickly, regardless of downstream latency.

Responsibilities:
- authenticate/validate requests (exact mechanism confirmed in Wave 03)
- normalize payload to internal schema
- guarantee idempotency at *event ingest*
- enqueue for async processing (SQS)
- return 2xx response fast

Non-goals:
- Do not call OpenAI or Shopify on the request thread.
- Do not send messages back to customers from the ingress function.

### 2.2 Processing layer (routing + automation)
Responsibilities:
- run intent classification and confidence scoring
- detect “Tier 0” topics (chargebacks/disputes, legal, threats, etc.) and immediately route
- run FAQ automation rules (order status/tracking only when deterministic match exists)
- maintain conversation automation state (e.g., waiting for order #)
- apply routing actions:
  - tags (primary routing primitive)
  - internal notes (audit trail)
  - assignment-to-agent only if required by your workflow

### 2.3 Data layer
- DynamoDB: idempotency keys, state machine markers, minimal audit metadata.
- S3 (optional): export aggregates, evaluation sets, and redacted transcripts if approved.
- CloudWatch: logs/metrics; alarms.

---

## 3) Design principles (production-grade)
1) **Ack fast, process async**
2) **Idempotent everywhere**
3) **Safe defaults**
   - never auto-close
   - no sensitive disclosure unless identity match is deterministic
4) **Bounded concurrency + backpressure**
5) **Explicit decision logging**
   - structured LLM outputs (JSON)
   - store the “why” (intent + confidence + rules matched)
6) **Observability-first**
   - metrics for routing accuracy, automation rate, backlog, retries, and rate-limit events

---

## 4) Why SQS FIFO (conversation-ordered processing)
Customers can send multiple messages quickly. If we process out of order, we can:
- send the wrong auto-reply (based on incomplete context)
- apply routing tags incorrectly
- create duplicate actions

**FIFO queue with MessageGroupId = conversation_id** provides a simple guardrail for early rollout.

---

## 5) “Keep it simple” scope alignment
For early rollout, we intentionally keep:
- only safe FAQ automation (order status/tracking when verified; “assist + route” for DNR)
- shipping exceptions routed to Returns Admin
- chargebacks/disputes routed to a dedicated team (no automation)

The architecture supports adding more automation later without redesign.
