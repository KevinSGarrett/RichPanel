# Hosting Options and Recommendation

Last updated: 2025-12-21

This project needs an integration middleware that:
- receives **inbound events/messages** from Richpanel
- performs **LLM-based classification** + **FAQ automation**
- writes updates/replies back to Richpanel (and optionally reads Shopify order status)
- is resilient to retries/duplicates, rate limits, and transient failures
- is simple to operate and cheap at current traffic, with room to scale

---

## Recommended deployment defaults (v1)

- **Primary AWS Region:** `us-east-2` (US East — Ohio)  
  Chosen to balance latency across US customers and support standard AWS services broadly.
- **Environment strategy:** separate AWS accounts for `dev`, `staging`, `prod` under AWS Organizations/Control Tower.
- **Channel urgency:** treat **LiveChat as real-time** for v1; treat all other channels as asynchronous by default.

---

## Options considered

### Option A — AWS Serverless (recommended)
**API Gateway (HTTP API)** → **Lambda (Ingress/Ack)** → **SQS (buffer)** → **Lambda (Processor/Worker)** → (OpenAI + Richpanel + Shopify)

Add:
- **DynamoDB** for idempotency + conversation state
- **Secrets Manager** for API keys/tokens
- **CloudWatch Logs/Metrics** (+ optional X-Ray)
- **DLQ** for failed events
- **EventBridge** for scheduled jobs (health checks, drift checks, retries, reporting)
- Optional: **WAF** in front of API Gateway for basic protection

**Why this fits:**
- Very low ops overhead; no servers/containers to manage.
- Great for bursty webhook traffic; scales automatically.
- Easy to decouple “ack quickly” from slower downstream processing.
- Cost-efficient at current volume (hundreds of msgs/hour per the heatmap).
- Can enforce safe throttles (SQS + reserved concurrency) to protect downstream rate limits.

**Primary risks (and how we mitigate):**
- Cold starts → keep functions small, avoid VPC when possible, and add provisioned concurrency only if needed.
- Duplicate events / retries → strong idempotency and “exactly-once at action layer” logic.
- Rate limits on Richpanel/Shopify/OpenAI → token-bucket limiter + bounded concurrency + backoff + queue buffering.

---

### Option B — AWS ECS/Fargate (containers)
**ALB/API Gateway** → **ECS Service (Ingress)** → internal queue (SQS/Redis) → **ECS Workers**

**Pros**
- More consistent latency (less cold start risk).
- Easier to run long-lived processes or heavy libraries.

**Cons**
- Higher operational overhead (cluster/service management).
- Higher baseline cost vs Lambda for low/medium workloads.
- Still needs queue + idempotency.

**When to choose instead of serverless**
- If routing/automation logic becomes very heavy (long CPU processing, multi-minute workflows),
- Or if we need strict control over concurrency, networking, and custom runtimes.

---

### Option C — EC2 (VM-based)
Generally not recommended unless there is a strong infrastructure constraint.

**Pros**
- Maximum control.
- Predictable performance.

**Cons**
- Highest ops burden (patching, scaling, HA, deploys).
- Overkill for current volumes and webhook-style workloads.

---

## Recommendation (best suggested default)
Choose **Option A: Serverless**.

### Recommended baseline stack (Wave 02 decision)
- **API Gateway HTTP API** as the external webhook endpoint (or API Gateway REST if features require).
- **Lambda Ingress** (validate + normalize + enqueue; respond 200 fast).
- **SQS FIFO Queue** for processing (MessageGroupId = `conversation_id`, DeduplicationId = `message_id`).
- **Lambda Worker** for classification + FAQ automation + Richpanel/Shopify write actions.
- **DynamoDB** tables for:
  - idempotency keys + action logs
  - conversation state / pending automation state (e.g., “waiting for order #”)
  - config snapshots (teams/tags/thresholds) if needed
- **DLQ** for messages that exceed retry policy.
- **Secrets Manager** for Richpanel API key, OpenAI API key, Shopify token(s).
- **CloudWatch** logs + metrics + alarms.

---

## Migration path (if we outgrow serverless)
This plan keeps a clean upgrade path:
- Keep **API contracts** and **queue formats** stable.
- If needed, swap Worker Lambda for an ECS/Fargate worker that consumes the same SQS queue.
- If needed, add Redis (ElastiCache) for caching/coordination — but avoid early unless necessary.

---

## What this decision unlocks
- Wave 03: we can design the inbound event contract and idempotency around SQS FIFO.
- Wave 04/05: we can safely do LLM calls off the webhook path, without risking Richpanel timeouts.
- Wave 07: we can compute capacity and cost based on clear AWS primitives.
