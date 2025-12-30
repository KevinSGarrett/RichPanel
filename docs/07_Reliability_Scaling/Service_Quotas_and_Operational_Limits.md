# Service Quotas and Operational Limits (Checklist)

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

This document lists the key AWS service limits that can unexpectedly block scaling and reliability.
We keep this practical: **what can cap us**, and **how we prevent surprises**.

> Note: Exact quotas can vary by account/region and can change over time.
> The purpose of this doc is to ensure we *track* and *verify* them during implementation.

---

## 1) AWS Lambda
Potential limit areas:
- account-level concurrent executions
- function reserved concurrency (misconfiguration can throttle throughput)
- timeout (max 15 minutes, but we will use much lower)
- payload limits (if using large event bodies)

Actions:
- record current account concurrency quota (dev/stage/prod)
- set reserved concurrency explicitly for worker
- ensure timeouts are consistent with SQS visibility timeout

---

## 2) API Gateway (HTTP API)
Potential limit areas:
- request rate and burst limits
- payload limits
- integration timeouts

Actions:
- configure throttling (rate + burst)
- monitor 4xx/5xx spikes
- enable WAF rate-based rule for abuse protection (prod)

---

## 3) SQS (FIFO)
Potential limit areas:
- throughput limits (message/sec; batching improves)
- in-flight messages (visibility timeout window)
- DLQ redrive configuration limits

Actions:
- confirm FIFO is appropriate for volume
- use MessageGroupId = conversation_id
- set DLQ redrive + alarms
- validate visibility timeout vs worker timeout

---

## 4) DynamoDB
Potential limit areas:
- provisioned vs on-demand throughput caps
- hot partitions (bad key design)
- TTL and PITR configuration

Actions:
- design keys to avoid hotspots
- use on-demand initially unless cost suggests provisioned
- enable TTL for idempotency/state tables
- optional: enable PITR for critical tables

---

## 5) CloudWatch Logs / Metrics
Potential limit areas:
- log ingestion cost and volume
- retention policy misconfig
- missing alarms

Actions:
- set log retention explicitly per environment
- create alarms for:
  - DLQ > 0
  - worker errors
  - queue age
  - 429 spikes
  - kill switch activation events

---

## 6) Vendor/API limits (non-AWS but critical)
- Richpanel API quota (rate limiting)
- OpenAI usage caps / rate limits (account-specific)
- Shopify API rate limits (if used)

Actions:
- document observed 429s and adjust concurrency
- implement backoff + Retry-After
- keep kill switch ready

---

## 7) Definition of done (for this checklist)
This doc is “done” when the implementation team has:
- recorded current quotas per environment
- confirmed we have headroom for 10× peak traffic
- set alarms for the first-order failure signals
