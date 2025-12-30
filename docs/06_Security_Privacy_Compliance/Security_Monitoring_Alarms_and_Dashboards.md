# Security Monitoring, Alarms, and Dashboards (v1)

Last updated: 2025-12-22  
Scope: **minimum** monitoring/alerting required for production safety (security + privacy + reliability signals)

This document defines the **minimum** CloudWatch alarms and dashboards we should configure so that:
- abuse / spoofed webhook traffic is detected quickly
- automation misbehavior is detected quickly
- queue backlogs and downstream outages are visible
- PII leakage signals are caught early (fail-safe)

> Wave 08 expands observability and analytics in depth. This file is the **security baseline**.

Related:
- Logging policy (PII-safe): `Logging_Metrics_Tracing.md`
- Incident response: `Incident_Response_Security_Runbooks.md`
- Kill switch / safe mode: `Kill_Switch_and_Safe_Mode.md`
- AWS baseline checklist: `AWS_Security_Baseline_Checklist.md`

---

## 1) Principles (security-first observability)

1. **Fail closed is better than silent failure**  
   If an alarm fires and we are unsure, we switch to **route-only safe mode** and investigate.

2. **No PII in metrics**  
   Metrics must not include raw message text, emails, phone numbers, addresses, tracking links, etc.

3. **Use a small number of high-signal alarms** (v1)  
   Too many alarms leads to alert fatigue and missed incidents.

4. **Every alarm has an owner and a runbook**  
   If we can’t answer “what do I do when this fires?”, the alarm is not ready.

---

## 2) Required dashboards (minimum)

### 2.1 Middleware — System Health (CloudWatch Dashboard)
**Panels (minimum):**
1) **Ingress**
- API Gateway requests
- API Gateway 5XX
- API Gateway latency (p95/p99 if available)
- Ingress Lambda errors + duration + throttles

2) **Queue**
- SQS FIFO `ApproximateAgeOfOldestMessage`
- SQS FIFO `ApproximateNumberOfMessagesVisible`
- DLQ `ApproximateNumberOfMessagesVisible`

3) **Worker**
- Worker Lambda errors
- Worker Lambda throttles
- Worker Lambda duration (p95/p99)
- Worker concurrent executions

4) **Data stores**
- DynamoDB throttled requests
- DynamoDB system errors
- DynamoDB consumed capacity vs provisioned (if provisioned)

5) **Business / safety**
- `routing.decisions_total` (custom metric)
- `automation.sent_total` (custom metric)
- `automation.blocked_total` (custom metric)
- `policy.tier0_detected_total` (custom metric)
- `fallback.route_only_total` (custom metric)

> **Implementation note:** Custom metrics should be emitted via Embedded Metric Format (EMF) or a simple CloudWatch PutMetricData wrapper.

### 2.2 Security — Abuse & Anomalies (CloudWatch Dashboard)
Minimum panels:
- requests/minute (API Gateway) + 4XX rate
- WAF blocked requests (if WAF is enabled)
- authentication failures (custom metric: `auth.invalid_token_total`)
- “PII redaction failures” (custom metric: `redaction.failed_total`)
- break-glass role assumptions (CloudTrail metric filter)

---

## 3) Minimum alarm set (v1)

> These thresholds are **starting defaults**. After 7–14 days of real traffic, tune them based on baseline behavior.

### 3.1 Ingress alarms

#### A1 — API Gateway 5XX errors (high severity)
- **Trigger:** 5XX > 0 for 5 minutes *or* 5XX rate > 1% for 5 minutes
- **Why:** indicates API Gateway/Lambda integration failures; can cause lost routing/automation
- **Action:** page / high-priority alert

Runbook (first actions):
- check API Gateway + Lambda health panels
- if widespread: set **safe_mode=true** (route-only) while investigating
- check recent deploys/config changes

#### A2 — Ingress Lambda errors (high severity)
- **Trigger:** Lambda errors >= 1 for 5 minutes (or >= 5 within 5 minutes)
- **Action:** high-priority alert

Runbook:
- check logs for exception type
- if secrets/auth errors: rotate token or verify secrets access
- if parsing errors: temporarily reduce payload (ticket_id-only)

#### A3 — Ingress Lambda throttles (medium/high)
- **Trigger:** throttles > 0 for 5 minutes
- **Why:** throttling on ingress risks slower ACKs and webhook retries/duplicates
- **Action:** medium severity; investigate concurrency settings

Runbook:
- verify reserved concurrency and account concurrency limits
- verify API Gateway throttling and burst settings
- confirm SQS send permissions not failing (permissions failures can look like retries)

### 3.2 Queue alarms (core reliability)

#### Q1 — SQS AgeOfOldestMessage (high severity)
- **Trigger (LiveChat safety):** age > 30 seconds for 3 datapoints (1 min)
- **Trigger (overall):** age > 120 seconds for 5 datapoints (5 min)
- **Why:** backlog means routing/automation latency will violate SLAs
- **Action:** high-priority alert

Runbook:
- check worker errors/throttles
- check downstream dependencies (Richpanel/OpenAI/Shopify) for outages/rate limits
- consider temporarily disabling automation (keep routing)

#### Q2 — DLQ has messages (high severity)
- **Trigger:** DLQ visible messages > 0
- **Action:** high-priority alert

Runbook:
- inspect DLQ payloads (redacted)
- identify systematic cause (schema changes, auth failures, rate-limit storms)
- if repeated: enable safe mode and fix root cause before replay

### 3.3 Worker alarms (downstream dependency sensitivity)

#### W1 — Worker Lambda errors (high severity)
- **Trigger:** errors >= 5 within 5 minutes (or any sustained error rate > 5%)
- **Why:** worker executes routing/automation; failures accumulate in queue
- **Action:** high-priority alert

Runbook:
- determine if OpenAI/Richpanel/Shopify outage vs internal bug
- if vendor outage: reduce retries and switch to route-only mode
- if bug: roll back deploy

#### W2 — Worker Lambda throttles (medium/high)
- **Trigger:** throttles > 0 for 5 minutes
- **Action:** medium severity (becomes high if queue age rises)

### 3.4 Data store alarms

#### D1 — DynamoDB throttled requests (medium/high)
- **Trigger:** throttled requests > 0 for 5 minutes
- **Why:** can break idempotency, state writes, and safety gating
- **Action:** medium; becomes high if errors increase

Runbook:
- verify capacity mode (on-demand recommended for v1)
- review access patterns; ensure hot partition is not created by bad keying

### 3.5 Security/privacy-specific alarms

#### S1 — Authentication failures spike (high severity)
- **Metric:** `auth.invalid_token_total` (custom)
- **Trigger:** > 20/min for 5 minutes (tune later)
- **Why:** could indicate scanning/attack or misconfigured Richpanel HTTP Target
- **Action:** high severity

Runbook:
- confirm Richpanel trigger config didn’t change
- if attack suspected: enable WAF (if not already), rotate token, and restrict allowed IPs if possible

#### S2 — Redaction failures (high severity)
- **Metric:** `redaction.failed_total` (custom)
- **Trigger:** > 0 for 5 minutes
- **Action:** high severity (privacy risk)

Runbook:
- enable safe mode (route-only)
- investigate the redaction function; patch before re-enabling automation

#### S3 — Break-glass role assumed (critical)
- **Source:** CloudTrail metric filter
- **Trigger:** any break-glass assume-role event
- **Action:** critical alert to leadership + owner

Runbook:
- confirm this was intentional
- record reason + duration
- post-incident: review and lock down

---

## 4) Log metric filters (optional, but recommended)
Use CloudWatch Logs metric filters for:
- `REDACTION_FAILED`
- `AUTH_INVALID_TOKEN`
- `POLICY_VIOLATION_BLOCKED_AUTOMATION`
- `DLQ_PUBLISH`

> Avoid generic “email regex” filters in v1 due to false positives and cost. Prefer **explicit structured log codes**.

---

## 5) Ownership and escalation (v1)
- Owner: **Developer (you)** for initial rollout
- Secondary: **Leadership** (for security incidents and break-glass alerts)
- During business hours: notify relevant department leads if customer-impacting

---

## 6) Wave 08 handoff
Wave 08 should expand:
- long-term analytics (precision/recall drift, per-team volumes)
- richer dashboards (customer experience metrics)
- anomaly detection models (optional)
- cost observability per intent/template
