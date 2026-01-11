# OpenAI Research (RichPanel Middleware)

**Goal:** provide an evidence-backed recommendation for **which OpenAI GPT‑5.x models (GPT‑5.1 / GPT‑5.2 family)** to use for each current + planned LLM workload in this repo, and **how to implement it safely**.

This directory is intentionally written as a “decision log + implementation plan” so model choices are auditable and repeatable.

---

## Contents

- `01_Current_Code_Audit.md`
  - Where OpenAI is used today (code + env vars)
  - Gating/logging/PII gaps vs policy

- `02_Roadmap_LLM_Workloads.md`
  - Planned LLM call graph (classifier, verifier, etc.)
  - Where each model fits in the pipeline

- `03_Model_Recommendations.md`
  - **Exact model IDs per workload** (grounded in repo docs + OpenAI docs evidence)
  - GPT‑5.x cascade strategy (nano → mini → 5.2)

- `04_Implementation_Plan.md`
  - How to wire GPT‑5.1/5.2 models into the middleware safely
  - How to centralize model config (env vars, versioning)
  - Migration plan: Chat Completions → Responses API + Structured Outputs
  - Logging changes required to meet “no body logging” policy

- `05_Cost_Latency_Estimates.md`
  - Cost model for **2,000–3,000 msgs/day** (your stated expectation)
  - Cross-check against repo’s observed ~5k/day in `docs/07_Reliability_Scaling/Cost_Model.md`

- `tools/list_openai_models.py`
  - Utility to list the **exact model IDs enabled** in your OpenAI org/project (so we can pin GPT‑5.1/5.2 snapshots confidently).

---

## Key repo sources (we rely on these)

- `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`
- `backend/src/integrations/openai/client.py`
- `backend/src/richpanel_middleware/automation/llm_routing.py`
- `backend/src/richpanel_middleware/automation/prompts.py`

---

## External evidence used

Because some OpenAI docs pages are intermittently blocked by bot protection in automated environments, we captured key fields (model IDs, snapshots, pricing) from the OpenAI docs site via accessibility snapshot on:

- `https://platform.openai.com/docs/models/gpt-5`

Evidence extracted includes:
- link to `GPT-5.1` docs (`/docs/models/gpt-5.1`)
- pricing quick comparison for GPT‑5 family (GPT‑5 / GPT‑5 mini / GPT‑5 nano)
- snapshot alias example: `gpt-5-2025-08-07`


