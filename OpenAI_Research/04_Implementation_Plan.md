# Implementation Plan: Integrating GPT‑5.1 / GPT‑5.2 into this middleware

This is the recommended engineering plan to adopt GPT‑5.x models **safely** in the current codebase.

---

## 0) Non-negotiables (from repo policy)

- **Fail closed** on any model error / parse failure / schema failure  
  (route-only / deterministic fallback).
- **No PII in logs** and **no OpenAI request/response bodies logged**  
  (`docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`).
- **Models are advisory; policy gates are authoritative**  
  (`docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`).
- **Classifier/verifier must use Structured Outputs + JSON Schema**  
  (`docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`).

---

## 1) Centralize model config (stop hardcoding)

### 1.1 Add a single “model config” module
Create something like:
- `backend/src/richpanel_middleware/llm/model_config.py`

It should:
- read env vars for each workload
- provide defaults from repo docs (GPT‑5 family)
- validate that model IDs are non-empty strings

### 1.2 Per-workload env vars (recommended)
Replace global `OPENAI_MODEL` usage with:
- `OPENAI_CLASSIFIER_MODEL` (default `gpt-5-mini`)
- `OPENAI_VERIFIER_MODEL` (default `gpt-5-mini`)
- `OPENAI_ROUTING_ADVISORY_MODEL` (default `gpt-5-mini`)
- `OPENAI_VARIANT_PICKER_MODEL` (default `gpt-5-nano`)
- `OPENAI_HEAVY_FALLBACK_MODEL` (default `gpt-5.2`)

Optionally allow explicit GPT‑5.1 pins:
- `gpt-5.1` / `gpt-5.1-mini` if available in your org.

---

## 2) Fix OpenAI logging (required before any customer-facing generation)

### 2.1 Current problem
`backend/src/integrations/openai/client.py` logs `message_excerpt` from the model response.

That violates:
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md` Rule D

### 2.2 Recommended fix
Add a parameter to `OpenAIClient.chat_completion` (or request object):
- `log_response_excerpt: bool = False` (default **False**)

Then:
- for routing/classifier/verifier: keep false (log only: status, latency, model)
- for local debugging only: optionally true behind an explicit dev-only flag

---

## 3) Migrate classifier/verifier to Responses API + Structured Outputs

Repo target is clear:
- use Responses API
- use structured output response format with JSON Schema

### 3.1 Why this matters
Our current code relies on “prompt says return JSON” and regex extraction.
Structured Outputs shifts correctness from “best effort” to “contract enforced.”

### 3.2 Implementation approach
Add a new client method (keeping Chat Completions for backward compatibility):
- `OpenAIClient.responses(request, ...)`

Where request supports:
- `model`
- `input` (messages)
- `text.format` / `json_schema` (or equivalent per OpenAI docs)
- `metadata`
- `store=false` (if supported by your API/account; see vendor doc)

---

## 4) Implement cascades (nano → mini → 5.2) only where it helps

Per repo design:
- start with `gpt-5-nano` for obvious messages
- escalate to `gpt-5-mini` on low confidence / multi-intent
- escalate to `gpt-5.2` only for rare ambiguity

Practical rule of thumb:
- only cascade if the first model can **abstain** cheaply and reliably
- don’t double-call on every message

---

## 5) Rollout plan (match repo governance)

Follow `docs/04_LLM_Design_Evaluation/Acceptance_Criteria_and_Rollout_Stages.md`:

1) Offline eval
2) Shadow mode
3) Tags only
4) Assignment (route-only)
5) Tier 1 safe-assist
6) Tier 2 verified automation

Every model change should include artifacts required by:
- `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`

---

## 6) About “unique/personalized” outbound copy

Repo policy is templates-only in early rollout. If you still want uniqueness:

- **Preferred**: template variants + model outputs only `variant_id`
- **Exception**: rewrite layer (must be explicitly approved)
  - only after logging + minimization are fixed
  - only rewrite deterministic body
  - strict JSON contract + length bounds + risk checks


