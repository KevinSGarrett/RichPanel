# Cost Model (Draft, Formula-Based)

Last updated: 2025-12-22
Last verified: 2025-12-21 — Updated with real traffic inputs from Agent Activity Heatmap.

This document estimates costs and identifies the main levers to control them.
Because vendor pricing can change, this model is **formula-based** with placeholders.

---

## 0) Real input volume (from Agent Activity Heatmap)

From the provided 7-day hourly volume file:
- Total inbound messages (7 days): **35,465**
- Average per day: **~5,066**
- Lowest day: **~3,928 (Sat)**
- Highest day: **~5,658 (Mon)**
- Peak hour: **430 messages/hour**

> Note: this is message volume, not “tickets”.
> A single conversation may contain multiple messages.

---

## 1) Cost drivers (ranked)

1) **OpenAI usage** (tokens, number of calls)
2) **AWS Lambda compute** (duration, memory)
3) **Queueing + storage** (SQS + DynamoDB)
4) Observability (logs, metrics, traces)

Richpanel API calls do not cost directly, but drive:
- latency
- rate-limit risk
- operational complexity

---

## 2) Key cost-control design decisions (recommended)

### 2.1 Use templates for responses (default)
We should **not** use LLM text generation for most customer replies.
Instead:
- LLM is used for **classification + decisioning** (which intent? confidence? required entities?)
- Customer-facing replies are **template-based** with deterministic inserts:
  - order status → “status + tracking link + tracking number”
  - safe-assist flows → “please provide order # / check with carrier / wait window”

This reduces token costs and makes behavior more consistent.

### 2.2 Two-stage model strategy (optional)
If we need more savings:
- stage 1: low-cost model routes obvious intents
- stage 2: larger model only for low-confidence or multi-intent messages

---

## 3) OpenAI cost model

### 3.1 Variables
Let:
- `M` = inbound messages per day (default: 5,066)
- `C` = classification calls per message (default: 1)
- `A` = “assistant generation” calls per message (default: 0 if template-based)
- `Tin` = avg input tokens per classification call
- `Tout` = avg output tokens per classification call
- `Pin` = price per 1K input tokens (model-specific)
- `Pout` = price per 1K output tokens (model-specific)

### 3.2 Daily OpenAI cost (classification-only default)
`Cost_openai_day = M * C * (Tin/1000 * Pin + Tout/1000 * Pout)`

### 3.3 Example token assumptions (for planning only)
These are placeholders to help reason about scale; we will replace them after eval runs:
- `Tin` ≈ 300–800 (includes system prompt + department list + rules)
- `Tout` ≈ 30–120 (structured JSON output)

### 3.4 Impact of adding LLM-generated replies (not recommended early)
If we add reply generation for some subset `p_auto`:
`Cost_openai_day += M * p_auto * (Tin_reply/1000 * Pin + Tout_reply/1000 * Pout)`

Where reply generation output tokens can be larger (200–600+).

---

## 4) AWS cost model (serverless baseline)

### 4.1 Lambda invocations
Per inbound message:
- 1× ingress Lambda invocation
- 1× worker Lambda invocation (sometimes more with retries)

Daily invocations:
- `Inv_ingress_day = M`
- `Inv_worker_day = M * (1 + retry_rate)`

### 4.2 Lambda compute
Let:
- `D_ingress` = avg ingress duration (seconds)
- `D_worker` = avg worker duration (seconds)
- `Mem_ingress`, `Mem_worker` = memory settings (GB)
- `Plambda` = Lambda price per GB-second (region-specific)

`Cost_lambda_day = Inv_ingress_day * D_ingress * Mem_ingress * Plambda
                 + Inv_worker_day  * D_worker  * Mem_worker  * Plambda`

> Ingress should be very fast (tens of ms). Worker dominates.

### 4.3 SQS
Per message, minimum:
- 1 send (ingress → queue)
- 1 receive/delete (worker)

So SQS requests/day ≈ `2M` (+ retries).

### 4.4 DynamoDB (v1)
Per message (typical):
- Idempotency: 1 write (conditional)
- Conversation state: 1 read+write or write-only update

So DynamoDB ops/day ≈ `~2–3M` (depending on implementation).

---

## 5) Cost guardrails (recommended)

See also: `Cost_Guardrails_and_Budgeting.md`

### 5.1 Budget + alerts (must)
- AWS Budgets alert thresholds: 50%, 80%, 100%
- OpenAI usage alert thresholds (daily and monthly caps)

### 5.2 Kill switch (must)
An environment variable / config flag to instantly:
- disable auto-replies
- optionally disable all Richpanel write actions (route-only or log-only)

### 5.3 “Shadow mode” (recommended early)
Before full rollout:
- run classification
- log decisions
- do not act

This lets us tune confidence thresholds and reduce the chance of expensive mistakes.

---

## 6) What we still need to finalize this model
- Confirm OpenAI model choice + pricing inputs
- Confirm Richpanel payload fields (message IDs, order IDs)
- Confirm whether Shopify fallback API will be used (and its call volume)
- Measure real token usage after we build prompt schemas (Wave 04)

