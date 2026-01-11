# Current OpenAI Usage Audit (Repo Truth)

This file answers:
- **Where do we call OpenAI today?**
- **How do we choose models today?**
- **Are we aligned with PII/logging policies?**
- **What must change before enabling GPT‑5.1/5.2 for production traffic?**

---

## 1) Where OpenAI is used today (code)

### 1.1 OpenAI HTTP client
- File: `backend/src/integrations/openai/client.py`
- Endpoint used: **Chat Completions** (`/v1/chat/completions`)
- Offline-first gates:
  - `safe_mode` (runtime)
  - `automation_enabled` (runtime)
  - `OPENAI_ALLOW_NETWORK` (env var)

**Env vars consumed by OpenAIClient**
- `OPENAI_ALLOW_NETWORK` (default false)
- `OPENAI_BASE_URL` (default `https://api.openai.com/v1`)
- `OPENAI_API_KEY_SECRET_ID` (default `rp-mw/<env>/openai/api_key`)
- `OPENAI_API_KEY` (optional override)
- `OPENAI_TIMEOUT_SECONDS` (default 10s)
- `OPENAI_MAX_ATTEMPTS` / `OPENAI_BACKOFF_SECONDS` / `OPENAI_BACKOFF_MAX_SECONDS`

### 1.2 LLM routing (advisory)
- File: `backend/src/richpanel_middleware/automation/llm_routing.py`
- Model selection today:
  - `model = os.environ.get("OPENAI_MODEL", DEFAULT_ROUTING_MODEL)`
  - `DEFAULT_ROUTING_MODEL = "gpt-4o-mini"`
- Gating:
  - blocks unless `safe_mode==false && automation_enabled==true && allow_network==true && outbound_enabled==true`
  - plus OpenAIClient-level block unless `OPENAI_ALLOW_NETWORK=true`

### 1.3 Prompt contracts / offline harness
- File: `backend/src/richpanel_middleware/automation/prompts.py`
- Model selection today:
  - `PromptConfig.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")`
- This module currently embeds **customer_profile + order_summary** into the system prompt context JSON.
  - That is fine for offline eval fixtures but **not acceptable for production LLM calls** under the repo’s PII minimization policy.

---

## 2) Important gaps vs policy (must address)

### 2.1 Logging violates “no OpenAI response bodies” policy
Repo policy is explicit:
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md` Rule D:
  - “Do not log OpenAI request/response bodies”

But the OpenAI client currently logs an excerpt of `response.message` (up to 200 chars):
- File: `backend/src/integrations/openai/client.py`
- Behavior: logs `openai.response` with `message_excerpt` if present.

**Impact**
- Any customer-facing generation (or rewrite) would leak content into logs.
- Even routing JSON may contain snippets of customer text if the model returns unexpected content.

**Action (required)**
- Add a “no excerpt” mode to OpenAIClient (e.g. `log_response_excerpt: bool = False`), default to false in production paths.

### 2.2 Docs vs code: `OPENAI_OUTBOUND_ENABLED` mismatch
Docs runbook mentions:
- `OPENAI_OUTBOUND_ENABLED` (`docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md`)

Code uses:
- `OPENAI_ALLOW_NETWORK`

**Action (recommended)**
- Standardize on one flag (or support both with clear precedence).

### 2.3 Model choice is hardcoded in multiple places (violates repo guidance)
Repo guidance says:
- “Model choice is config, not code”
  - `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`

But we currently hardcode defaults in:
- `llm_routing.py` (`DEFAULT_ROUTING_MODEL = "gpt-4o-mini"`)
- `prompts.py` (`OPENAI_MODEL`, default `"gpt-4o-mini"`)

**Action (recommended)**
- Centralize model selection per-workload (routing vs classifier vs verifier vs rewrite).

---

## 3) Current “shipped vs roadmap” note (important)

The repo explicitly states:
- Shipped v1 worker uses deterministic routing (no live classifier call)
  - `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

So the **primary GPT‑5.x integration work** is actually roadmap items:
- classifier (`mw_decision_v1`)
- verifier (`mw_tier2_verifier_v1`)
- policy engine + rollout gates

---

## 4) Immediate prerequisites before enabling GPT‑5.1 / GPT‑5.2

1) **Fix OpenAI logging** (no response excerpts; no bodies).
2) **Centralize model config** per workload (see `04_Implementation_Plan.md`).
3) **Minimize LLM input** per PII policy:
   - no full `customer_profile` objects
   - no order/tracking IDs in classifier prompts (use booleans + coarse status buckets)
4) Move classifier/verifier to:
   - **Responses API + Structured Outputs** (repo requirement)
   - see `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`


