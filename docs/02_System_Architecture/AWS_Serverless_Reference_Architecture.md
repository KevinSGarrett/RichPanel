# AWS Serverless Reference Architecture (Recommended)

Last updated: 2025-12-21
Last verified: 2025-12-21 — Added DynamoDB state model references + v1 safety controls.

This is the **best-suggested default AWS stack** for the Richpanel middleware.
It is designed for:
- fast webhook acknowledgement (ACK-fast)
- safe async processing
- rate-limit protection
- low operational burden
- easy evolution (swap worker to ECS later if required)

---

## 0) Region and environment defaults

### 0.1 Primary AWS Region (recommended)
**Primary region (v1):** `us-east-2` (US East — Ohio)

Rationale:
- US-wide customer base → balanced latency
- supports all required serverless primitives

**Secondary/DR region (optional later):** `us-west-2`

> For early rollout we operate **single-region, multi-AZ**.

### 0.2 AWS account / environment strategy (recommended)
**Recommended:** separate AWS accounts:
- `dev`
- `staging`
- `prod`

**Current state:**
- AWS Organizations / Control Tower are **not set up yet**
- v1 plan: set up **AWS Organizations (no Control Tower)** and create the accounts
- Owner of the management account: **you (developer)**

See: `AWS_Organizations_Setup_Plan_No_Control_Tower.md`

---

## 1) Components (baseline)

### 1.1 Edge / ingress
- **API Gateway (HTTP API)** — public endpoint for Richpanel HTTP Target / webhook
- Optional: **AWS WAF** — basic protections (bot filtering, rate limits)

Design choice:
- Keep Lambdas **out of VPC** unless required (reduces cold starts).

### 1.2 Compute
**Lambda — `rp-mw-ingress`**
- Responsibility: validate + normalize + persist idempotency + enqueue
- Timeout: 3–6 seconds (but returns far faster in practice)
- Memory: 256–512 MB
- Concurrency: high (it does not call OpenAI/Shopify; it should not bottleneck)

**Lambda — `rp-mw-worker`**
- Trigger: SQS event source mapping
- Responsibility: routing + FAQ decisioning + downstream calls (Richpanel/OpenAI/Shopify)
- Timeout: 30–60 seconds (tune)
- Memory: 512–1024 MB
- **Reserved concurrency (v1): start low (e.g., 5)** and tune after load tests

### 1.3 Queueing
**SQS FIFO queue — `rp-mw-events.fifo`**
- `MessageGroupId = conversation_id` (ensures per-conversation ordering)
- `MessageDeduplicationId = message_id` (or stable event ID) when available
- Visibility timeout: >= worker timeout (e.g., 90s)

Recommended additions:
- **DLQ**: `rp-mw-events-dlq` (poison messages)
- Optional retry queues (if we want controlled backoff): `rp-mw-retry-60s`, `rp-mw-retry-10m`

### 1.4 Storage (state + idempotency)
**DynamoDB**
- Table A: `rp_mw_idempotency` (required)
- Table B: `rp_mw_conversation_state` (recommended)
- Table C: `rp_mw_audit_actions` (optional)

Schema details:
- `DynamoDB_State_and_Idempotency_Schema.md`

**Secrets Manager**
- Richpanel API key
- OpenAI API key
- Shopify token (if used)

> No secrets in code, no secrets in logs.

### 1.5 Observability (baseline)
- CloudWatch Logs (structured JSON logs)
- CloudWatch Metrics + Alarms:
  - SQS `ApproximateAgeOfOldestMessage`
  - DLQ depth > 0
  - Worker errors > threshold
  - 429 rate per downstream
- Optional: AWS X-Ray tracing

---

## 2) Internal processing contract (SQS message envelope)

Before Wave 03 integration is finalized, we standardize an internal event envelope.

**Minimal v1 envelope**
```json
{
  "event_id": "evt:rp:<conversation_id>:<message_id_or_hash>",
  "received_at": "2025-12-21T00:00:00Z",
  "conversation_id": "string",
  "channel": "livechat|email|social|tiktok|unknown",
  "customer": {
    "email": "optional",
    "phone": "optional",
    "id": "optional"
  },
  "message": {
    "id": "optional",
    "created_at": "optional",
    "text": "string (may be truncated for safety)",
    "attachments": [
      {
        "type": "image|pdf|other",
        "url": "optional",
        "size_bytes": "optional"
      }
    ]
  },
  "richpanel": {
    "tags": ["optional"],
    "assignee_id": "optional"
  },
  "meta": {
    "attempt": 0,
    "source": "richpanel_http_target"
  }
}
```

Rules:
- Avoid embedding large attachment payloads in the event.
- Truncate message text to a safe max length (prevent payload bloat).
- Do not include raw PII in logs; redact before logging.

---

## 3) IAM roles & least privilege (baseline)

### 3.1 Ingress Lambda role
Minimum:
- `sqs:SendMessage` to `rp-mw-events.fifo`
- `dynamodb:PutItem` to `rp_mw_idempotency` (conditional write)
- `secretsmanager:GetSecretValue` (if inbound signature secret is used)

### 3.2 Worker Lambda role
Minimum:
- `dynamodb:GetItem/PutItem/UpdateItem` to state/idempotency tables
- `secretsmanager:GetSecretValue` for API keys

---

## 4) Safety controls (v1 must-have)

### 4.1 Kill switch
A single environment flag that disables:
- auto replies (always)
- optionally all Richpanel “write actions” (route-only mode)

This is the fastest way to stop harm during an incident.

### 4.2 Shadow mode
A mode where we:
- compute routing + confidence
- log decisions
- **do not act**

Recommended for early rollout to validate accuracy.

### 4.3 Circuit breakers
If downstream error rate exceeds thresholds:
- stop calling it temporarily
- fallback to human routing

---

## 5) Scaling knobs (how we tune)
- Worker reserved concurrency (primary knob)
- SQS batch size (keep small for predictable latency; e.g., 1–5)
- Separate queues for “real-time lane” (optional for LiveChat)
- Token bucket limiter for Richpanel/OpenAI/Shopify (see `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`)

---

## 6) When to add ECS/Fargate (not v1)
Consider migrating only if:
- worker processing becomes consistently long-running (near Lambda limits)
- dependencies cause unacceptable cold starts
- we need strict predictable p95 at high throughput

Even then:
- keep API Gateway + SQS as stable primitives
- swap only the worker

