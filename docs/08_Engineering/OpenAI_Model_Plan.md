# OpenAI Model Plan

**Status:** Active  
**Last updated:** 2026-01-12  
**Owner:** Engineering + PM  
**Related docs:**
- `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`
- `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`
- `PM_REHYDRATION_PACK/OpenAI_Research/`

---

## Purpose

This document defines the **authoritative model selection strategy** for all OpenAI LLM workloads in the RichPanel middleware. It ensures:

- **Enforceable defaults:** All LLM calls use GPT‑5.x models only (no GPT‑4 fallback)
- **Per-workload configuration:** Each use case has its own model environment variable
- **Safe migration path:** Clear phases from env vars → Responses API → template variants
- **Audit trail:** Model choices are documented, versioned, and tied to repo code

---

## Model Matrix (Per Workload)

### Current Workloads

| Workload | Purpose | Default Model | Env Var | Code Reference |
|----------|---------|--------------|---------|----------------|
| **Routing/Classification** | Intent detection + department routing | `gpt-5.2-chat-latest` | `OPENAI_ROUTING_MODEL` or `OPENAI_MODEL` | `backend/src/richpanel_middleware/automation/llm_routing.py` |
| **Reply Rewriter** (optional) | Style polishing of deterministic replies | `gpt-5.2-chat-latest` | `OPENAI_REPLY_REWRITE_MODEL` or `OPENAI_MODEL` | `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py` |
| **OpenAI Client** | Generic LLM client | `gpt-5-mini` | `OPENAI_MODEL` | `backend/src/integrations/openai/client.py` |

### Planned Roadmap Workloads

| Workload | Purpose | Recommended Model | Env Var | Notes |
|----------|---------|------------------|---------|-------|
| **Primary Classifier** (`mw_decision_v1`) | Intent + tier recommendation + template selection | `gpt-5-mini` | `OPENAI_CLASSIFIER_MODEL` | Strict JSON Schema via Responses API |
| **Tier 2 Verifier** (`mw_tier2_verifier_v1`) | Safety check before shipping/status disclosure | `gpt-5-mini` | `OPENAI_VERIFIER_MODEL` | Conditional; only when classifier recommends Tier 2 |
| **Cheap Pre-pass** (optional) | Fast triage for obvious messages | `gpt-5-nano` | `OPENAI_PREPASS_MODEL` | Escalate to mini on low confidence |
| **Heavy Fallback** (rare) | High-stakes ambiguity resolution | `gpt-5.2` | `OPENAI_HEAVY_FALLBACK_MODEL` | Only for complex edge cases |
| **Variant Picker** (future) | Select template variant ID (not text) | `gpt-5-nano` | `OPENAI_VARIANT_PICKER_MODEL` | Templates-only policy compliant |

---

## Enforced Default Rule

**All LLM workloads MUST default to GPT‑5.x models only.**

- **Allowed models:**
  - `gpt-5-nano` (cheapest, highest throughput)
  - `gpt-5-mini` (recommended default for classification/verification)
  - `gpt-5` / `gpt-5-2025-08-07` (snapshot alias)
  - `gpt-5.1` / `gpt-5.1-mini` (if available in your OpenAI org)
  - `gpt-5.2` (highest capability, rare use)
  
- **Prohibited models:**
  - `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo` (legacy)
  - Any non-GPT‑5 family models

**Rationale:**
- GPT‑5 family offers better accuracy, lower latency, and lower cost per token than GPT‑4 equivalents
- Standardizing on one model family simplifies governance, cost modeling, and rollout
- Repo policy requires latest models for production LLM workloads

**Enforcement:**
- CI checks validate that code defaults are GPT‑5.x
- Env var overrides are permitted for dev/testing but must be documented
- See: `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`

---

## Code Module Mapping

### 1. LLM Routing (`llm_routing.py`)

**Current state:**
- File: `backend/src/richpanel_middleware/automation/llm_routing.py`
- Default model: `DEFAULT_ROUTING_MODEL = "gpt-5.2-chat-latest"` (line 48)
- Env var: `OPENAI_MODEL` (fallback to default)
- API: Chat Completions (`/v1/chat/completions`)

**Target state (Phase 1):**
- Migrate to Responses API + Structured Outputs
- Add explicit `OPENAI_ROUTING_MODEL` env var (separate from global `OPENAI_MODEL`)
- Emit strict JSON Schema per `mw_decision_v1` contract

**Required changes:**
1. Add `OPENAI_ROUTING_MODEL` env var support (default: `gpt-5-mini`)
2. Migrate `suggest_llm_routing()` to Responses API
3. Add JSON Schema validation for routing output
4. Update logging to exclude response bodies (PII compliance)

---

### 2. Reply Rewriter (`llm_reply_rewriter.py`)

**Current state:**
- File: `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`
- Default model: `os.environ.get("OPENAI_REPLY_REWRITE_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-5.2-chat-latest")` (line 21-23)
- Env var: `OPENAI_REPLY_REWRITE_MODEL` (already per-workload!)
- API: Chat Completions

**Target state (Phase 1):**
- Migrate to Responses API + Structured Outputs
- Add strict JSON Schema for rewrite output (body, confidence, risk_flags)
- Fix logging (message excerpts disabled by default; only gated, redacted debug logging allowed)

**Required changes:**
1. Migrate `rewrite_reply()` to Responses API
2. Add JSON Schema for `ReplyRewriteResult` contract
3. Keep message excerpts disabled by default; allow only an opt-in debug flag (non-production only), with truncated excerpts that exclude request bodies and user content; flag must never be enabled in production

---

### 3. OpenAI Client (`openai/client.py`)

**Current state:**
- File: `backend/src/integrations/openai/client.py`
- Default: No hardcoded model (passed by caller)
- API: Chat Completions only

**Target state (Phase 1):**
- Add new method: `OpenAIClient.responses()` for Responses API
- Keep `chat_completion()` for backward compatibility
- Fix logging violation: message excerpts disabled by default; only gated, truncated debug logging allowed

**Required changes:**
1. Add `responses()` method with JSON Schema support
2. Remove response body logging (PII compliance)
3. Add `log_response_excerpt` flag (default: `False`), only usable for explicit debug (non-production only), never in production; truncate and exclude request/user bodies

**Logging fix (CRITICAL for PII compliance):**

Current violation:

```436:441:backend/src/integrations/openai/client.py
            preview = ""
            if response.message:
                preview = _truncate(response.message, limit=200)
            elif response.raw:
                preview = _truncate(json.dumps(response.raw, sort_keys=True), limit=200)
            if preview:
                extra["message_excerpt"] = preview
```

This violates `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md` Rule D: "Do not log OpenAI request/response bodies."

**Fix (current plan after Agent C gate):** Message excerpts are disabled by default. A short excerpt may be logged only when an explicit debug flag is enabled. The debug flag is non-production only. Excerpts must be truncated and must exclude request bodies or any user content. The flag must never be enabled in production.

---

## Phase Plan (Migration Strategy)

### Phase 0: Env Vars + Defaults (Current)

**Status:** Partially complete  
**Timeframe:** Complete before any production LLM traffic

**Goals:**
- ✅ Per-workload env vars exist (`OPENAI_REPLY_REWRITE_MODEL`)
- ⚠️ Global `OPENAI_MODEL` still used as fallback in routing
- ⚠️ All defaults are GPT‑5.x (current: `gpt-5.2-chat-latest`)
- ❌ Logging still includes response excerpts (PII violation)

**Required actions:**
1. Add `OPENAI_ROUTING_MODEL` env var to `llm_routing.py`
2. Add `OPENAI_CLASSIFIER_MODEL`, `OPENAI_VERIFIER_MODEL` for roadmap workloads
3. Keep OpenAI client message excerpts gated: default disabled; debug flag only outside production; truncate and exclude request/user bodies
4. Update env var documentation in runbooks

**Acceptance criteria:**
- All workloads have explicit env vars (no shared `OPENAI_MODEL` fallback)
- CI checks validate GPT‑5.x defaults
- No response bodies in logs

---

### Phase 1: Responses API + Structured Outputs (Target)

**Status:** Not started  
**Timeframe:** Before classifier/verifier production rollout

**Goals:**
- Migrate routing + rewrite to Responses API
- Add strict JSON Schema for all LLM outputs
- Enable `store=false` flag (if supported by OpenAI account)

**Required actions:**
1. Add `OpenAIClient.responses()` method with JSON Schema support
2. Migrate `suggest_llm_routing()` to Responses API
3. Migrate `rewrite_reply()` to Responses API
4. Add JSON Schema validation for `mw_decision_v1` and `mw_tier2_verifier_v1`
5. Update offline eval harness to test Structured Outputs

**Acceptance criteria:**
- All production LLM calls use Responses API (not Chat Completions)
- Strict JSON Schema enforced on outputs
- Offline eval passes with Structured Outputs
- No regression in latency/accuracy

**References:**
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/04_LLM_Design_Evaluation/schemas/mw_decision_v1.schema.json`

---

### Phase 2: Template Variants + Confidence Tuning (Future)

**Status:** Planned  
**Timeframe:** Post-production rollout

**Goals:**
- Add template variant library (N approved versions per `template_id`)
- Use LLM only to select `variant_id` (not generate text)
- Tune confidence thresholds based on production data

**Required actions:**
1. Expand template library with variants (tone, formality, length)
2. Add `OPENAI_VARIANT_PICKER_MODEL` env var (default: `gpt-5-nano`)
3. Add variant picker LLM call (outputs `variant_id` only)
4. Tune confidence thresholds via offline eval + A/B testing
5. Add cascade logic (nano → mini → 5.2) if needed

**Acceptance criteria:**
- Template variants cover 90%+ of common scenarios
- LLM never generates free-form customer-facing text
- Confidence calibration reduces false positives/negatives
- Cost per message stays below budget targets

**References:**
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

---

## CI Enforcement (GPT-5.x-only)

- `scripts/verify_openai_model_defaults.py` fails if any GPT-4 family defaults (`gpt-4`, `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`) appear in `backend/src` or `config`, or if GPT model tokens there are not GPT-5 family prefixes.
- `scripts/run_ci_checks.py` runs this guard in both local and `--ci` modes; any regression to GPT-4 defaults breaks CI-equivalent checks.
- Docs, OpenAI_Research, and REHYDRATION_PACK history are excluded from this guard to avoid blocking historical references.

---

## Cost & Latency Model

### Pricing (GPT‑5 Family)

Source: `https://platform.openai.com/docs/models/gpt-5` (captured 2026-01-12)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|-------|----------------------|------------------------|-------|
| `gpt-5-nano` | $0.05 | TBD | Cheapest; highest throughput |
| `gpt-5-mini` | $0.25 | TBD | Recommended default |
| `gpt-5` | $1.25 | $10.00 | Full capability |
| `gpt-5.2` | (assume same as `gpt-5`) | (assume same as `gpt-5`) | Heavy fallback |

**Note:** Output token pricing for mini/nano not captured in quick comparison. Confirm via `https://openai.com/api/pricing/` before production rollout.

### Volume Assumptions

- **Expected volume:** 2,000–3,000 messages/day (user-stated)
- **Observed volume:** ~5,066 messages/day (from `docs/07_Reliability_Scaling/Cost_Model.md`)
- **Token budget per message:**
  - Classifier input: 300–800 tokens (taxonomy + customer text)
  - Classifier output: 30–120 tokens (strict JSON only)

### Daily Cost Estimate (Single Classifier Call)

For 3,000 msgs/day with `gpt-5-mini`:
- Input: 3,000 × 600 tokens = 1.8M tokens/day × $0.25/1M = **$0.45/day** (input only)
- Output: 3,000 × 80 tokens = 240K tokens/day × (TBD) = **$???/day**

**Total estimated cost:** ~$1–2/day for single-call classifier (confirm output pricing).

### Latency Targets

- **Classifier:** < 500ms p95 (strict JSON, short output)
- **Verifier:** < 300ms p95 (even shorter than classifier)
- **Rewrite:** < 800ms p95 (longer output, not on critical path)

**Mitigation:**
- Use `max_tokens` limits to bound output size
- Enable caching where supported
- Monitor p95/p99 latency in production

---

## Governance & Updates

### Model Update Policy

**All model changes must follow:**
- `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`

**Key requirements:**
1. Offline eval on representative traffic (>= 100 samples)
2. Shadow mode validation (log LLM suggestions, don't act on them)
3. Confidence threshold tuning before production
4. Rollback plan if accuracy/latency regresses

### Change Control

**Minor changes** (env var updates, threshold tuning):
- PR with CI passing + @cursor review
- No offline eval required if model ID unchanged

**Major changes** (API migration, model family switch):
- Full offline eval + shadow mode + stakeholder approval
- Update this doc with phase status
- Add migration checklist to `PLAN_CHECKLIST.md`

### Audit Trail

**Every model change must include:**
1. Update to this doc (model matrix + phase status)
2. Git commit with descriptive message
3. PR with evidence (eval results, latency graphs, cost impact)
4. Update to `CHANGELOG.md` if production-impacting

---

## Quick Reference

### Current Defaults (as of 2026-01-12)

```bash
# Routing
OPENAI_MODEL=gpt-5.2-chat-latest                    # fallback (global)
# OPENAI_ROUTING_MODEL not yet implemented

# Reply rewriter
OPENAI_REPLY_REWRITE_MODEL=gpt-5.2-chat-latest      # explicit per-workload

# Roadmap (not yet implemented)
# OPENAI_CLASSIFIER_MODEL=gpt-5-mini
# OPENAI_VERIFIER_MODEL=gpt-5-mini
# OPENAI_PREPASS_MODEL=gpt-5-nano
# OPENAI_HEAVY_FALLBACK_MODEL=gpt-5.2
# OPENAI_VARIANT_PICKER_MODEL=gpt-5-nano
```

### Roadmap Targets

```bash
# Production defaults (Phase 1)
OPENAI_CLASSIFIER_MODEL=gpt-5-mini
OPENAI_VERIFIER_MODEL=gpt-5-mini
OPENAI_ROUTING_MODEL=gpt-5-mini
OPENAI_REPLY_REWRITE_MODEL=gpt-5-mini

# Optional workloads (Phase 2)
OPENAI_PREPASS_MODEL=gpt-5-nano
OPENAI_HEAVY_FALLBACK_MODEL=gpt-5.2
OPENAI_VARIANT_PICKER_MODEL=gpt-5-nano
```

---

## Related Work Packages

- **W12-EP06-T063:** Confidence calibration / threshold tuning (offline)
- **W12-EP06-T064:** Offline eval harness + regression gates in CI
- **EP06:** LLM routing + policy engine (full roadmap)

---

## See Also

- `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md` — repo design principles
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md` — Responses API requirement
- `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md` — change control
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md` — logging policy
- `PM_REHYDRATION_PACK/OpenAI_Research/` — evidence-backed analysis
