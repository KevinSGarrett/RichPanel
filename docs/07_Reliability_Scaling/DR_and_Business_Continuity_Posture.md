# Disaster Recovery and Business Continuity Posture (v1)

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

This project’s v1 is designed to be reliable without over-engineering.
We choose a **single-region, multi-AZ** posture with clear operational fallbacks.

Primary region (v1): `us-east-2` (Ohio)

---

## 1) What “failure” means for this system

### 1.1 Component failures (most common)
- OpenAI degraded/unavailable
- Richpanel API degraded/rate-limited
- Shopify API degraded (optional path)
- Lambda errors due to deploy/regression
- SQS backlog due to downstream slowdown

### 1.2 Region-wide outage (rare)
- AWS region outage impacting API Gateway/Lambda/SQS/DynamoDB

---

## 2) v1 posture (recommended)

### 2.1 Single region, multi-AZ by default
Most AWS serverless services are multi-AZ within a region.

We rely on:
- SQS durability for buffering
- DynamoDB durability for idempotency/state
- API Gateway for stable ingress endpoint

### 2.2 Recovery goals (draft)
- **RTO (restore service):** minutes to hours (depending on outage type)
- **RPO (data loss):** minimal for queued events; idempotency/state data should be recoverable

Because this system is **middleware**, the primary “business continuity” plan is:
- if automation is down, agents can still respond manually in Richpanel
- if routing is down, use temporary fallback routing rules in Richpanel

---

## 3) Backups and recovery

### 3.1 DynamoDB
- TTL limits data growth (idempotency/state are time-bounded)
- optional PITR for critical tables (decision based on compliance needs)

### 3.2 Configuration as code
- prompts, schemas, templates live in repo
- infrastructure lives in IaC (Terraform/CDK/etc.)

Recovery is primarily redeploying IaC, not restoring data.

---

## 4) Multi-region DR (v2 option; not planned for v1)
We can add a second region later if needed.

Typical v2 design:
- active/passive with manual or automated failover
- replicated secrets/config
- region-specific API endpoints + DNS failover
- careful handling of idempotency across regions

Decision trigger for multi-region:
- business requires it (SLA)
- region outage impact is unacceptable
- cost/complexity is justified

---

## 5) Incident playbook (high level)
If the middleware is degraded:
1) enable kill switch (stop auto-replies)
2) switch to route-only or log-only
3) if routing unavailable, enable temporary Richpanel fallback routing rules
4) after recovery, replay DLQ items if safe and needed

Full incident response is documented in Wave 10.
