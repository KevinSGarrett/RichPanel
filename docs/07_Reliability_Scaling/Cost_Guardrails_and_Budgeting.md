# Cost Guardrails and Budgeting (v1)

Last updated: 2025-12-22  
Status: **Wave 07 (in progress)**

This document defines cost controls that prevent “runaway spend” from:
- message spikes
- retry storms
- prompt/token bloat
- logging explosions

Related:
- `Cost_Model.md` (formula-based)
- Wave 06 kill switch: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

---

## 1) Guardrail layers

### 1.1 Hard guardrails (must-have)
- **Kill switch** to disable auto-replies immediately (route-only continues)
- **Reserved concurrency** caps worker execution (prevents stampede)
- **SQS DLQ** with alarms (prevents infinite retry loops)
- **Log retention** set explicitly (avoid infinite retention)

### 1.2 Soft guardrails (recommended)
- “Shadow mode” rollout (log-only) to calibrate before acting
- token usage monitoring (tokens/message p95)
- template-level disable switches (`template_enabled.<id>`)

---

## 2) AWS cost controls

### 2.1 AWS Budgets
Set budget alerts per environment (dev/stage/prod):
- 50% (warning)
- 80% (warning)
- 100% (critical)

### 2.2 CloudWatch log volume control
- default: metadata logs only (no raw message bodies)
- log retention:
  - dev: 7–14 days
  - staging: 14–30 days
  - prod: 30–90 days (depending on compliance)

### 2.3 Concurrency-based spend cap
Because Lambda and downstream calls scale with concurrency, the worker reserved concurrency is itself a spend cap.

---

## 3) OpenAI cost controls

### 3.1 Default to classification-only + templates
We avoid LLM reply generation costs by:
- using LLM for decision output only
- rendering replies from templates

### 3.2 Token budget monitoring
Track:
- input tokens/message
- output tokens/message
- total tokens/day

Alert if:
- p95 tokens/message increases > 2× baseline
- daily tokens exceed budget threshold

### 3.3 “Disable LLM” fallback (if needed)
If OpenAI spend or outage becomes a risk:
- route everything to a default triage team
- disable auto-replies
- optionally enable simple keyword rules for top intents (order status, returns)

---

## 4) Definition of done (Wave 07)
Wave 07 cost guardrails are “done” when:
- budgets + alerts are documented
- kill switch behavior is documented and testable
- token usage metrics are defined for dashboards (Wave 08)
