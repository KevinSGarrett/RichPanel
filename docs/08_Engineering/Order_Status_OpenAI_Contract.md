# Order Status OpenAI Contract

**Status:** Canonical  
**Last Updated:** 2026-01-20  
**Risk Level:** R3 (production automation with external LLM calls)

This document codifies **where, how, and why** OpenAI is used in the Order Status automation pipeline. It serves as the definitive reference to prevent "forgetting" critical OpenAI integration points during development, deployment, and incident response.

---

## Executive Summary

The Order Status automation uses OpenAI (GPT-5.2) in **two critical phases**:

1. **Intent Classification (Routing)**: Classify customer messages to determine if they are asking about order status
2. **Reply Generation (Rewrite)**: Transform deterministic template replies into unique, empathetic customer responses

Both phases are **fail-closed by default** and operate in **advisory mode** until explicitly enabled for production use.

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ Inbound Ticket (Richpanel Webhook)                                 │
│   ├─ conversation_id                                                │
│   ├─ customer message (PII-minimized for routing)                   │
│   └─ metadata (tags, status, etc.)                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 1: OpenAI Intent Classification (Routing)                    │
│   Module: llm_routing.py                                            │
│   Function: suggest_llm_routing()                                   │
│                                                                      │
│   Input:  customer_message (first 2000 chars)                       │
│   Output: {intent, department, confidence, response_id}             │
│                                                                      │
│   Gates (all must pass):                                            │
│     ✓ safe_mode = False                                             │
│     ✓ automation_enabled = True                                     │
│     ✓ allow_network = True                                          │
│     ✓ outbound_enabled = True                                       │
│                                                                      │
│   Model: OPENAI_MODEL (default: gpt-5.2-chat-latest)                │
│   API Key: rp-mw/<env>/openai/api_key (Secrets Manager)             │
│                                                                      │
│   Evidence Required:                                                │
│     - llm_called = true                                             │
│     - response_id (format: chatcmpl-*)                              │
│     - confidence >= 0.85 (for primary routing)                      │
│     - final_intent in {order_status_tracking, order_status_no_...}  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 2: Order Lookup (Deterministic)                              │
│   Module: order_lookup.py                                           │
│   Source: Shopify Admin API                                         │
│                                                                      │
│   Output: order_summary {status, tracking, fulfillment, ETA}        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 3: Deterministic Draft Generation                            │
│   Module: delivery_estimate.py                                      │
│   Function: build_tracking_reply() / build_no_tracking_reply()      │
│                                                                      │
│   Output: template_reply (deterministic, fact-based)                │
│     - Contains order status, tracking info, or ETA                  │
│     - NO customer PII in the template                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 4: OpenAI Reply Rewrite (Unique Message)                     │
│   Module: llm_reply_rewriter.py                                     │
│   Function: rewrite_reply()                                         │
│                                                                      │
│   Input:  template_reply (deterministic draft)                      │
│   Output: {rewritten_body, confidence, risk_flags, response_id}     │
│                                                                      │
│   Gates (all must pass):                                            │
│     ✓ OPENAI_REPLY_REWRITE_ENABLED = true                           │
│     ✓ safe_mode = False                                             │
│     ✓ automation_enabled = True                                     │
│     ✓ allow_network = True                                          │
│     ✓ outbound_enabled = True                                       │
│                                                                      │
│   Model: OPENAI_REPLY_REWRITE_MODEL (fallback: OPENAI_MODEL)        │
│   API Key: rp-mw/<env>/openai/api_key (Secrets Manager)             │
│                                                                      │
│   Evidence Required:                                                │
│     - rewrite_attempted = true                                      │
│     - rewrite_applied = true (or fallback_used + error_class)       │
│     - response_id (format: chatcmpl-*)                              │
│     - confidence >= 0.7 (default threshold)                         │
│     - NO suspicious_content in risk_flags                           │
│                                                                      │
│   Fail-Closed Behavior:                                             │
│     If rewrite fails or confidence < threshold:                     │
│       → Use original deterministic draft (safe fallback)            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 5: Close Ticket + Send Reply                                 │
│   Module: pipeline.py                                               │
│   Function: execute_order_status_reply()                            │
│                                                                      │
│   Actions (production-read-only BLOCKS these):                      │
│     - Update ticket status to "resolved" / "closed"                 │
│     - Add tags: mw-auto-replied, mw-order-status-answered           │
│     - Post reply (rewritten or deterministic draft)                 │
│                                                                      │
│   Safety: NEVER sends replies in shadow mode / safe mode            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 6: Follow-up Routing (Loop Prevention)                       │
│   Module: pipeline.py                                               │
│   Function: _should_skip_order_status()                             │
│                                                                      │
│   Behavior:                                                         │
│     If ticket already has mw-auto-replied tag:                      │
│       → Route to Email Support Team (NO duplicate auto-reply)       │
│       → Add tags: route-email-support-team,                         │
│                   mw-skip-followup-after-auto-reply                 │
│                                                                      │
│   Evidence:                                                         │
│     - routed_to_support = true                                      │
│     - NO additional middleware reply                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Code Map

### 1. OpenAI Routing (Intent Classification)

**Primary Module:** `backend/src/richpanel_middleware/automation/llm_routing.py`

**Key Functions:**

- `suggest_llm_routing()` — Main entry point for LLM-based routing
  - Gates: safe_mode, automation_enabled, allow_network, outbound_enabled
  - Returns: `LLMRoutingSuggestion` with intent, department, confidence, response_id
- `compute_dual_routing()` — Computes both deterministic + LLM routing
  - Decides which to use based on `OPENAI_ROUTING_PRIMARY` flag
  - Returns: `RoutingDecision` + `RoutingArtifact` (audit record)

**Prompt Contract:**

- System prompt: `ROUTING_SYSTEM_PROMPT` (lines 143-166)
  - Defines valid intents and departments
  - Requires JSON response with {intent, department, confidence, reasoning}
  - **PII Policy:** "Do NOT include any personal data, order numbers, or customer details in your response"
- User prompt: First 2000 chars of customer message (truncated for safety)

**Configuration:**

| Env Var                              | Purpose                               | Default             |
|--------------------------------------|---------------------------------------|---------------------|
| `OPENAI_MODEL`                       | Model for routing                     | gpt-5.2-chat-latest |
| `OPENAI_ROUTING_PRIMARY`             | Use LLM routing as primary            | false               |
| `OPENAI_ROUTING_CONFIDENCE_THRESHOLD`| Minimum confidence for primary routing| 0.85                |

**Evidence Fields (logged + persisted):**

- `llm_called` (bool) — True if network call was made
- `response_id` (str) — OpenAI response ID (format: `chatcmpl-*`)
- `response_id_unavailable_reason` (str) — Reason if response_id is missing
- `model` (str) — Actual model used (from response)
- `confidence` (float) — LLM confidence score (0.0-1.0)
- `final_intent` (str) — Classified intent (e.g., `order_status_tracking`)
- `dry_run` (bool) — True if gated (no network call)
- `gated_reason` (str) — Gate that blocked the call

---

### 2. OpenAI Reply Rewrite (Unique Message Generation)

**Primary Module:** `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`

**Key Functions:**

- `rewrite_reply()` — Main entry point for reply rewriting
  - Gates: OPENAI_REPLY_REWRITE_ENABLED, safe_mode, automation_enabled, allow_network, outbound_enabled
  - Returns: `ReplyRewriteResult` with body, confidence, risk_flags, response_id

**Prompt Contract:**

- System prompt (lines 100-108):
  - "You rewrite Richpanel customer replies. Preserve facts and promises, avoid new commitments, keep it concise and professional."
  - Requires strict JSON response: `{body, confidence, risk_flags}`
  - **PII Policy:** "If the input seems risky or contains sensitive data, add 'suspicious_content' to risk_flags and keep the original tone."
- User prompt: "Rewrite this reply safely:\n\n{trimmed}" (first 2000 chars)

**Configuration:**

| Env Var                                 | Purpose                               | Default             |
|-----------------------------------------|---------------------------------------|---------------------|
| `OPENAI_REPLY_REWRITE_MODEL`            | Model for rewriting                   | (fallback to OPENAI_MODEL) |
| `OPENAI_MODEL`                          | Fallback model                        | gpt-5.2-chat-latest |
| `OPENAI_REPLY_REWRITE_ENABLED`          | Enable reply rewriting                | false               |
| `OPENAI_REPLY_REWRITE_CONFIDENCE_THRESHOLD` | Minimum confidence to apply rewrite | 0.7                 |
| `OPENAI_REPLY_REWRITE_MAX_TOKENS`       | Max tokens for response               | 400                 |
| `OPENAI_REPLY_REWRITE_MAX_CHARS`        | Max chars in rewritten body           | 1000                |

**Evidence Fields (logged + persisted):**

- `rewrite_attempted` (bool) — True if rewrite was attempted (gates passed)
- `rewrite_applied` (bool) — True if rewritten body was used
- `fallback_used` (bool) — True if deterministic draft was used instead
- `response_id` (str) — OpenAI response ID
- `response_id_unavailable_reason` (str) — Reason if missing
- `model` (str) — Actual model used
- `confidence` (float) — Rewrite confidence (0.0-1.0)
- `risk_flags` (list[str]) — Flags like `suspicious_content`, `truncated`
- `error_class` (str) — Exception class if request failed
- `gated_reason` (str) — Gate that blocked the call

**Fail-Closed Behavior:**

If rewrite fails or confidence < threshold:
- Falls back to **deterministic draft** (safe, fact-based reply)
- Logs `fallback_used=true` + `error_class` (no message text)

---

### 3. Pipeline Orchestration

**Primary Module:** `backend/src/richpanel_middleware/automation/pipeline.py`

**Key Functions:**

- `_order_status_pipeline()` (lines 309-460) — Orchestrates the full pipeline
  - Step 1: Dual routing (deterministic + LLM)
  - Step 2: Order lookup (Shopify)
  - Step 3: Deterministic draft generation
  - Step 4: LLM reply rewrite
  - Step 5: Reply execution (or skip in shadow mode)
- `execute_order_status_reply()` — Sends reply + closes ticket
  - **Shadow mode:** logs actions but does NOT send replies
  - **Production:** updates ticket status, adds tags, posts reply

**Configuration References:**

- `OPENAI_ROUTING_PRIMARY` — Enables LLM routing as primary (default: false)
- `OPENAI_REPLY_REWRITE_ENABLED` — Enables reply rewriting (default: false)

---

## Configuration Map

### Environment Variables

#### OpenAI Model Selection

| Env Var                       | Used By         | Purpose                          | Default             |
|-------------------------------|-----------------|----------------------------------|---------------------|
| `OPENAI_MODEL`                | All modules     | Primary OpenAI model             | gpt-5.2-chat-latest |
| `OPENAI_ROUTING_PRIMARY`      | llm_routing.py  | Use LLM routing as primary       | false               |
| `OPENAI_REPLY_REWRITE_MODEL`  | llm_reply_rewriter.py | Model for rewriting (overrides OPENAI_MODEL) | (none) |

#### OpenAI Behavior Flags

| Env Var                              | Used By               | Purpose                               | Default |
|--------------------------------------|-----------------------|---------------------------------------|---------|
| `OPENAI_REPLY_REWRITE_ENABLED`       | llm_reply_rewriter.py | Enable reply rewriting                | false   |
| `OPENAI_ROUTING_CONFIDENCE_THRESHOLD`| llm_routing.py        | Min confidence for primary routing    | 0.85    |
| `OPENAI_REPLY_REWRITE_CONFIDENCE_THRESHOLD` | llm_reply_rewriter.py | Min confidence to apply rewrite | 0.7     |
| `OPENAI_ALLOW_NETWORK`               | openai/client.py      | Allow network calls                   | false   |

#### OpenAI Client Configuration

| Env Var                        | Used By          | Purpose                          | Default |
|--------------------------------|------------------|----------------------------------|---------|
| `OPENAI_BASE_URL`              | openai/client.py | OpenAI API base URL              | https://api.openai.com/v1 |
| `OPENAI_API_KEY_SECRET_ID`     | openai/client.py | Secrets Manager secret ID        | rp-mw/\<env\>/openai/api_key |
| `OPENAI_API_KEY`               | openai/client.py | Direct API key (overrides Secrets Manager) | (none) |
| `OPENAI_TIMEOUT_SECONDS`       | openai/client.py | Request timeout                  | 10.0    |
| `OPENAI_MAX_ATTEMPTS`          | openai/client.py | Max retry attempts               | 3       |
| `OPENAI_BACKOFF_SECONDS`       | openai/client.py | Initial backoff delay            | 0.25    |
| `OPENAI_BACKOFF_MAX_SECONDS`   | openai/client.py | Max backoff delay                | 2.0     |

---

### AWS Secrets Manager

**Secret Path Pattern:** `rp-mw/<env>/openai/api_key`

**Environments:**

- `dev`: `rp-mw/dev/openai/api_key`
- `staging`: `rp-mw/staging/openai/api_key`
- `prod`: `rp-mw/prod/openai/api_key`

**Loader:** `backend/src/integrations/openai/client.py` (lines 349-387)

**Fallback Order:**

1. `OPENAI_API_KEY` env var (if set)
2. Secrets Manager lookup (default)
3. Fail-closed: return `dry_run=true`, `reason=missing_api_key`

**Required IAM Permissions (Worker Lambda Role):**

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": [
    "arn:aws:secretsmanager:us-east-2:*:secret:rp-mw/<env>/openai/api_key-*"
  ]
}
```

---

## PII Policy

### Routing (Intent Classification)

**Input to OpenAI:**

- **Customer message** (first 2000 chars)
- **May include:** customer text about orders, questions, complaints
- **Must NOT include:** full ticket bodies with personal details

**Output from OpenAI:**

- **Intent + department + confidence**
- **Reasoning** (truncated to 500 chars for safety)
- **NO PII allowed:** System prompt explicitly forbids including order numbers, customer details, or personal data

**Safety Measures:**

- Message truncation (2000 chars max)
- Prompt instructs LLM to exclude PII in reasoning
- Response reasoning is truncated to 500 chars before logging

---

### Reply Rewrite (Unique Message Generation)

**Input to OpenAI:**

- **Deterministic draft reply** (template-based, fact-only)
- **May include:** order status, tracking info, ETA
- **Must NOT include:** raw customer messages, emails, phone numbers

**Output from OpenAI:**

- **Rewritten reply body** (max 1000 chars)
- **Confidence + risk_flags**
- **PII detection:** Scans for suspicious patterns (SSN, credit cards, passwords)

**Safety Measures:**

- Input is deterministic draft (no raw customer PII)
- Output scanned for suspicious patterns (SUSPICIOUS_PATTERNS regex, lines 32-40)
- If `suspicious_content` detected → reject rewrite, use deterministic draft

---

## Production-Read-Only Shadow Mode

**Critical Safety Rule:** OpenAI calls are permitted in shadow mode for **evaluation and proof generation**, but **replies are NEVER sent** to customers.

### Shadow Mode Behavior

**Routing:**

- ✅ OpenAI routing calls proceed (if gates pass)
- ✅ Evidence logged (response_id, confidence, intent)
- ❌ NO routing decisions applied to actual tickets

**Reply Rewrite:**

- ✅ OpenAI rewrite calls proceed (if gates pass)
- ✅ Evidence logged (response_id, confidence, rewritten_body)
- ❌ NO replies sent to customers
- ❌ NO ticket status changes
- ❌ NO tags applied

**Proof Mode:**

- ✅ Captures full audit artifacts (routing + rewrite evidence)
- ✅ Writes to DynamoDB (idempotency, state, audit tables)
- ✅ Generates proof JSON with OpenAI evidence
- ❌ Absolutely no outbound writes to Richpanel/Shopify

**See:** `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`

---

## Proof Requirements

### Order Status Proof Must Show OpenAI Usage

An order_status proof run is **NOT acceptable** if:

1. **Routing did NOT call OpenAI** (unless OpenAI is intentionally disabled AND explicitly documented)
2. **Reply rewrite did NOT call OpenAI** (if "unique message" requirement is in force)

### Required Evidence in Proof JSON

**Routing Evidence:**

```json
{
  "openai": {
    "routing": {
      "llm_called": true,
      "model": "gpt-5.2-chat-latest",
      "confidence": 0.92,
      "final_intent": "order_status_tracking",
      "response_id": "chatcmpl-abc123xyz",
      "response_id_unavailable_reason": null,
      "dry_run": false,
      "gated_reason": null
    }
  }
}
```

**Rewrite Evidence:**

```json
{
  "openai": {
    "rewrite": {
      "rewrite_attempted": true,
      "rewrite_applied": true,
      "fallback_used": false,
      "model": "gpt-5.2-chat-latest",
      "confidence": 0.88,
      "response_id": "chatcmpl-def456uvw",
      "response_id_unavailable_reason": null,
      "risk_flags": [],
      "error_class": null,
      "dry_run": false,
      "gated_reason": null
    }
  }
}
```

**Fallback Case (rewrite failed but routing succeeded):**

```json
{
  "openai": {
    "routing": {
      "llm_called": true,
      "response_id": "chatcmpl-abc123xyz",
      "confidence": 0.92
    },
    "rewrite": {
      "rewrite_attempted": true,
      "rewrite_applied": false,
      "fallback_used": true,
      "error_class": "OpenAIRequestError",
      "confidence": 0.0,
      "response_id": null,
      "response_id_unavailable_reason": "request_failed"
    }
  }
}
```

---

## Validation Harness

**Script:** `scripts/dev_e2e_smoke.py`

**Order Status Scenarios:**

- `order_status_tracking` — Requires OpenAI routing + rewrite evidence
- `order_status_no_tracking` — Requires OpenAI routing + rewrite evidence

**Default Flags:**

- `--require-openai-routing` (default: true)
- `--require-openai-rewrite` (default: true)

**Override Flags (debugging only):**

- `--no-require-openai-routing` — Skip OpenAI routing check
- `--no-require-openai-rewrite` — Skip OpenAI rewrite check

**PASS_STRONG Criteria:**

- Webhook accepted (HTTP 200/202)
- Idempotency + state + audit records observed
- Routing intent is `order_status_tracking` or `order_status_no_tracking`
- **OpenAI routing:** `llm_called=true` + `response_id` present
- **OpenAI rewrite:** `rewrite_applied=true` + `response_id` present (or `fallback_used=true` + `error_class`)
- Ticket status changed to `resolved` / `closed`
- Reply evidence observed (message_count delta > 0 OR last_message_source=middleware)
- NO skip/escalation tags added

**See:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (lines 474-610)

---

## OpenAI Usage Compliance

### Model Evolution

**Current Model:** `gpt-5.2-chat-latest` (default)

**Roadmap:**

- **GPT-5.2** is used for both routing and rewrite
- **GPT-5.5+** may require prompt adjustments (especially for max_completion_tokens vs max_tokens)
- **Future models:** Update `DEFAULT_ROUTING_MODEL` and `DEFAULT_MODEL` constants

**Model-Specific Handling:**

- `gpt-5.*` models use `max_completion_tokens` instead of `max_tokens` (lines 88-91 in openai/client.py)
- `gpt-5.*` models may omit `metadata` field (line 92-93)
- `gpt-5.*` models may suppress `temperature` if 0.0 (lines 81-84)

---

### Cost Management

**Routing:**

- ~256 tokens per request (max_tokens=256)
- Input: ~500-1000 tokens (customer message + system prompt)
- Estimated cost: $0.01-0.02 per request (GPT-5.2 pricing)

**Rewrite:**

- ~400 tokens per request (max_tokens=400)
- Input: ~200-500 tokens (deterministic draft + system prompt)
- Estimated cost: $0.015-0.025 per request (GPT-5.2 pricing)

**Total per Order Status Resolution:** ~$0.025-0.045

**Volume Estimate:** 100-500 order status tickets/day → $2.50-$22.50/day

---

### Rate Limiting

**OpenAI Rate Limits (GPT-5.2):**

- Requests per minute: 500 (org-level)
- Tokens per minute: 2,000,000 (org-level)

**Middleware Behavior:**

- **429 (rate limit exceeded):** Retry with exponential backoff (max 3 attempts)
- **Backoff:** 0.25s → 0.5s → 1.0s (with jitter)
- **Max backoff:** 2.0s (configurable via `OPENAI_BACKOFF_MAX_SECONDS`)

**Circuit Breaker (future):**

- If OpenAI failures exceed 50% over 5 minutes → disable OpenAI routing/rewrite
- Fall back to deterministic routing + templates
- Alert on-call

---

## Monitoring & Observability

### CloudWatch Metrics (Proposed)

**Routing Metrics:**

- `OpenAIRoutingCalls` (Count) — Total OpenAI routing calls
- `OpenAIRoutingErrors` (Count) — Failed routing calls (429, 5xx, timeout)
- `OpenAIRoutingLatency` (Milliseconds) — P50, P95, P99
- `OpenAIRoutingConfidence` (Value) — Average confidence score

**Rewrite Metrics:**

- `OpenAIRewriteCalls` (Count) — Total rewrite calls
- `OpenAIRewriteApplied` (Count) — Rewrites actually used
- `OpenAIRewriteFallback` (Count) — Fallback to deterministic draft
- `OpenAIRewriteLatency` (Milliseconds) — P50, P95, P99

### CloudWatch Logs

**Log Groups:**

- `/aws/lambda/rp-mw-<env>-worker`

**Log Events:**

- `openai.routing.suggestion` — Routing result (intent, confidence, response_id)
- `openai.rewrite.applied` — Rewrite applied (confidence, response_id)
- `openai.rewrite.fallback` — Fallback to deterministic (reason, error_class)
- `openai.request_failed` — Request failure (status, error, attempt)
- `openai.retry` — Retry attempt (attempt, retry_in)

**Log Fields (always present):**

- `event_id`, `conversation_id` — For correlation
- `fingerprint` — Prompt fingerprint (SHA256 prefix, no secrets)
- `response_id` — OpenAI response ID (when available)
- `model` — Actual model used
- `dry_run` — True if gated
- `gated_reason` — Gate that blocked (if any)

---

## Incident Response

### Scenario: OpenAI Outage

**Symptoms:**

- 429 / 5xx errors from OpenAI API
- Routing / rewrite latency spikes
- `OpenAIRoutingErrors` / `OpenAIRewriteErrors` metrics elevated

**Immediate Actions:**

1. Disable OpenAI routing: Set `OPENAI_ROUTING_PRIMARY=false` (if enabled)
2. Disable OpenAI rewrite: Set `OPENAI_REPLY_REWRITE_ENABLED=false` (if enabled)
3. Verify fallback to deterministic routing + templates
4. Monitor worker errors for cascading failures

**Rollback:**

- Deploy Lambda environment variable updates via CDK
- Confirm worker logs show `gated_reason=network_blocked` or `dry_run=true`

---

### Scenario: PII Leak

**Symptoms:**

- Customer PII (email, phone, SSN) detected in OpenAI request/response logs
- Security alert from log scanning

**Immediate Actions:**

1. **Stop all OpenAI calls:** Set `OPENAI_ALLOW_NETWORK=false` globally
2. **Rotate OpenAI API key:** Revoke compromised key, generate new key, update Secrets Manager
3. **Audit logs:** Search CloudWatch Logs for PII patterns
4. **Redact logs:** Request log deletion from AWS support (if necessary)
5. **Notify security team:** Incident report + impact assessment

**Prevention:**

- Review prompt templates for PII leakage
- Add PII detection to proof JSON scanner
- Enforce stricter input truncation limits

---

### Scenario: Cost Spike

**Symptoms:**

- OpenAI billing alert triggered
- Unexpectedly high volume of routing/rewrite calls

**Immediate Actions:**

1. Check CloudWatch Metrics: `OpenAIRoutingCalls`, `OpenAIRewriteCalls`
2. Identify anomalous traffic (conversation_id, event_id patterns)
3. Disable OpenAI if runaway loop detected
4. Review idempotency logic (duplicate event prevention)

**Investigation:**

- Check for retry storms (429 → retry → 429 loop)
- Check for duplicate webhook ingestion
- Review DynamoDB idempotency table for missing deduplication

---

## Change Control

### Adding New OpenAI Calls

**Process:**

1. **Document intent:** Update this contract with new use case
2. **Add gating:** All new OpenAI calls must be gated (safe_mode, automation_enabled, allow_network)
3. **Add evidence:** Log `llm_called`, `response_id`, `model`, `dry_run`, `gated_reason`
4. **Update proof harness:** Add validation checks to `scripts/dev_e2e_smoke.py`
5. **PR requirements:** R3+ risk label, Claude gate, Bugbot, Codecov, CI green

---

### Changing OpenAI Models

**Process:**

1. **Document model:** Update `DEFAULT_ROUTING_MODEL` / `DEFAULT_MODEL` constants
2. **Test prompts:** Verify prompt compatibility (especially GPT-5 → GPT-6 transitions)
3. **Update proof JSON:** Ensure new model shows in proof artifacts
4. **Deploy to dev:** Test with `--scenario order_status_tracking`
5. **Deploy to staging:** Verify PASS_STRONG proof
6. **Production:** Only after staging proof + PM approval

**Breaking Changes:**

- **max_tokens → max_completion_tokens:** Update `to_payload()` logic
- **Metadata removal:** Verify logging still captures required fields
- **Response format changes:** Update `_parse_llm_response()` / `_parse_response()`

---

### Disabling OpenAI (Emergency)

**Immediate (no deploy):**

```bash
# Set via AWS Console (Lambda → Environment Variables)
OPENAI_ROUTING_PRIMARY=false
OPENAI_REPLY_REWRITE_ENABLED=false
# or
OPENAI_ALLOW_NETWORK=false
```

**Permanent (requires deploy):**

```typescript
// infra/cdk/lib/richpanel-middleware-stack.ts
workerLambda.addEnvironment("OPENAI_ROUTING_PRIMARY", "false");
workerLambda.addEnvironment("OPENAI_REPLY_REWRITE_ENABLED", "false");
```

**Verification:**

- Check worker logs for `gated_reason=automation_disabled` or `dry_run=true`
- Verify no `openai.routing.suggestion` or `openai.rewrite.applied` logs
- Confirm fallback to deterministic routing + templates

---

## Related Documentation

- **OpenAI Model Plan:** `docs/08_Engineering/OpenAI_Model_Plan.md`
- **CI and Actions Runbook:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (proof requirements)
- **Production Read-Only Shadow Mode:** `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- **Order Status Automation Spec:** `docs/05_FAQ_Automation/Order_Status_Automation.md`
- **Secrets and Environments:** `docs/08_Engineering/Secrets_and_Environments.md`

---

## Revision History

| Date       | Author        | Change                                     |
|------------|---------------|--------------------------------------------|
| 2026-01-20 | Cursor Agent  | Initial version (B48 documentation task)   |
