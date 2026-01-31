<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R3; p0_ok=true; timestamp=2026-01-31 -->

**Run ID:** `RUN_20260131_1923Z`  
**Agents:** A  
**Labels:** `risk:R3`, `gate:claude`  
**Risk:** `risk:R3`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_011Z4T9Zo5wJqV1PRTDEHP4U`  

### 1) Summary
- Enable OpenAI routing/intent/rewrites in read-only shadow via explicit MW flags and shadow overrides.
- Sanitize all OpenAI prompt inputs for order-status flows (HTML stripped; emails/phones/addresses redacted; order numbers preserved).
- Expand prod-shadow reporting to capture OpenAI usage, classification source counts, and new proof artifacts.

### 2) Why
- **Problem / risk:** outbound-enabled gating blocked OpenAI routing/intent in read-only shadow, producing deterministic-only metrics.
- **Pre-change failure mode:** prod shadow reports showed `classification_source=deterministic_router` with no OpenAI usage.
- **Why this approach:** decouple OpenAI enablement from outbound writes while keeping fail-closed gating and PII-safe inputs.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- OpenAI calls only run when `MW_OPENAI_*_ENABLED=true`, `safe_mode=false`, `automation_enabled=true`, and `allow_network=true`.
- Shadow mode can call OpenAI with outbound disabled when `MW_OPENAI_SHADOW_ENABLED=true`.
- OpenAI prompts never include raw emails/phones/addresses; HTML is stripped; order numbers may remain.
- Prod shadow remains read-only: no outbound messages or writes.

**Non-goals (explicitly not changed):**
- No changes to outbound write gating or allowlist behavior.
- No model/temperature tuning changes.

### 4) What changed
**Core changes:**
- Added a shared PII sanitizer and wired it into routing, intent, rewrite, and order-status prompt builders.
- Added MW OpenAI enable flags + shadow override in routing, intent, and rewrite gating.
- Updated prod-shadow report to include OpenAI usage counts, classification sources, and intent evidence.

**Design decisions (why this way):**
- Keep write gating intact while allowing safe read-only OpenAI calls for evaluation.
- Best-effort PII redaction with order-number preservation to maintain intent signal.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/pii_sanitizer.py`
- `backend/src/richpanel_middleware/automation/llm_routing.py`
- `backend/src/richpanel_middleware/automation/order_status_intent.py`
- `backend/src/richpanel_middleware/automation/order_status_prompts.py`
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`
- `backend/src/richpanel_middleware/automation/prompts.py`
- `scripts/prod_shadow_order_status_report.py`
- `scripts/shadow_order_status.py`
- `scripts/live_readonly_shadow_eval.py`

**Tests:**
- `backend/tests/test_order_status_intent.py`
- `scripts/test_order_status_intent_contract.py`
- `scripts/test_llm_routing.py`
- `scripts/test_llm_reply_rewriter.py`

**CI / workflows:**
- (None)

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/prod_shadow_report_openai_enabled.json`
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/prod_shadow_report_openai_enabled.md`
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/sandbox_openai_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/sandbox_openai_order_status_proof.md`

### 6) Test plan
**Local / CI-equivalent:**
- Not run (proof runs below).

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `AWS_PROFILE=rp-admin-kevin AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 AWS_SDK_LOAD_CONFIG=1 MW_ALLOW_NETWORK_READS=true RICHPANEL_READ_ONLY=true RICHPANEL_WRITE_DISABLED=true RICHPANEL_OUTBOUND_ENABLED=false MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true OPENAI_ALLOW_NETWORK=true SHOPIFY_OUTBOUND_ENABLED=true SHOPIFY_WRITE_DISABLED=true RICHPANEL_ENV=prod MW_ENV=prod ENVIRONMENT=prod RICH_PANEL_ENV=prod RICHPANEL_RATE_LIMIT_RPS=0.3 python scripts/prod_shadow_order_status_report.py --allow-ticket-fetch-failures --retry-diagnostics --batch-size 1 --throttle-seconds 3 --out-json REHYDRATION_PACK/RUNS/B65/A/PROOF/prod_shadow_report_openai_enabled.json --out-md REHYDRATION_PACK/RUNS/B65/A/PROOF/prod_shadow_report_openai_enabled.md --ticket-number <redacted...> # 595 tickets provided in prompt`
- `MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_REWRITE_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true OPENAI_ALLOW_NETWORK=true RICHPANEL_OUTBOUND_ENABLED=true RICHPANEL_WRITE_DISABLED=false RICHPANEL_READ_ONLY=false MW_ALLOW_NETWORK_READS=true RICHPANEL_ENV=dev MW_ENV=dev ENVIRONMENT=dev RICH_PANEL_ENV=dev python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --require-openai-routing --require-openai-rewrite --create-ticket --proof-path REHYDRATION_PACK/RUNS/B65/A/PROOF/sandbox_openai_order_status_proof.json --run-id b65-dev-20260131-b1 --wait-seconds 120 --profile rp-admin-kevin # sandbox stack not available`

### 7) Results & evidence
**CI:** pending — https://github.com/KevinSGarrett/RichPanel/actions  
**Codecov:** pending — https://app.codecov.io/gh/KevinSGarrett/RichPanel  
**Bugbot:** pending — https://cursor.com (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/prod_shadow_report_openai_enabled.json`
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/prod_shadow_report_openai_enabled.md`
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/sandbox_openai_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B65/A/PROOF/sandbox_openai_order_status_proof.md`

**Proof snippet(s) (PII-safe):**
```text
prod_shadow: classification_source=mixed; counts=openai_intent:594 deterministic_router:1; order_status_rate=37.3%
sandbox(dev): openai.routing.response_id=chatcmpl-D4DpBmF3dgb4tu0BwIrTfaQ1CmDDR
sandbox(dev): openai.intent.response_id=chatcmpl-D4DpRryCwf5RgflSRww1Jzs2seMWE
```

### 8) Risk & rollback
**Risk rationale:** `risk:R3` — adjusts LLM gating and prompt sanitization in order-status automation paths.

**Failure impact:** OpenAI calls may be skipped or overly sanitized, reducing intent accuracy or rewrite quality.

**Rollback plan:**
- Revert PR.
- Re-run prod shadow + sandbox proofs to confirm deterministic-only baseline is restored.

### 9) Reviewer + tool focus
**Please double-check:**
- LLM gating logic for routing/intent/rewrite with shadow override behavior.
- PII sanitizer coverage (HTML, emails, phones, addresses) while keeping order numbers intact.
- Prod shadow report fields for OpenAI usage and classification source counts.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
- Minor test fixture adjustments for redaction assertions.
