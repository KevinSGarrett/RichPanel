<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-03 -->

**Run ID:** `RUN_20260204_0011Z`  
**Agents:** C  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01SmW5tbtr59eVHY8NQk8v8M`  
**Anthropic request id:** `req_011CXnJcr5EycBbnkP743JNc`

### 1) Summary
- Restored deterministic order-status coverage via expanded routing rules, delivery-issue detection, and nested message extraction.
- Hardened order-number extraction to prefer explicit patterns and avoid date-like standalone digits.
- Added deterministic fallback in prod shadow reporting plus a skip-OpenAI flag for baseline runs.
- Extended the eval harness with ticket-id inputs, CSV output, and redacted excerpts; generated PII-safe eval artifacts.

### 2) Why
- **Problem / risk:** deterministic order-status rate was 0% in B68, masking fallback performance when OpenAI is gated.
- **Pre-change failure mode:** prod shadow deterministic runs classified zero order-status tickets despite order-number matches.
- **Why this approach:** fix deterministic routing + extraction and ensure shadow reports fall back to deterministic intent when LLM is unavailable.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Read-only prod shadow remains GET-only; no outbound writes.
- LLM calls only run when MW flags allow; `--skip-openai-intent` explicitly forces deterministic baseline.
- Proof artifacts remain PII-safe (redacted excerpts, hashed ids).

**Non-goals (explicitly not changed):**
- No changes to OpenAI prompt contracts or confidence thresholds.
- No changes to Shopify/Richpanel client behavior outside shadow reporting.

### 4) What changed
**Core changes:**
- Deterministic router now recognizes broader order-status language (ETA/delays/delivery issues) and address-change intent.
- Order-number extraction adds `order id`/standalone 6–8 digit support and skips date-like candidates.
- Shadow report uses deterministic routing when LLM intent is not called and supports `--skip-openai-intent`.
- Eval harness supports ticket-id lists, CSV output, and redacted excerpts.

**Design decisions (why this way):**
- Keep LLM gating intact while ensuring deterministic fallback is measurable and safe.
- Prefer explicit order-number patterns to reduce false matches on dates/phones.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/router.py`
- `backend/src/richpanel_middleware/commerce/order_lookup.py`
- `scripts/prod_shadow_order_status_report.py`
- `scripts/eval_order_status_intent.py`

**Tests:**
- `backend/tests/test_router_order_status_precedence.py`
- `backend/tests/test_order_lookup_order_id_resolution.py`
- `scripts/test_eval_order_status_intent.py`

**CI / workflows:**
- (None)

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B69/C/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_dataset.jsonl`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_results.json`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_results.csv`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_run_attempts.md`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_deterministic.json`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_openai.json`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_summary.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m pytest backend/tests/test_router_order_status_precedence.py backend/tests/test_order_lookup_order_id_resolution.py scripts/test_eval_order_status_intent.py`
- `python scripts/eval_order_status_intent.py --dataset REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_dataset.jsonl --output REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_results.json --output-csv REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_results.csv`
- `python scripts/run_ci_checks.py --ci` (fails: generated files changed after regen; dirty worktree with pre-existing changes)

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `OPENAI_API_KEY=<redacted> MW_ALLOW_NETWORK_READS=true RICHPANEL_READ_ONLY=true RICHPANEL_WRITE_DISABLED=true RICHPANEL_OUTBOUND_ENABLED=false MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true SHOPIFY_OUTBOUND_ENABLED=true SHOPIFY_WRITE_DISABLED=true SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com python scripts/prod_shadow_order_status_report.py --env prod --allow-ticket-fetch-failures --ticket-number <redacted>...` (8 x 25-ticket batches, deterministic + OpenAI)

### 7) Results & evidence
**CI:** `validate` ✅  
**Codecov:** `codecov/patch` ✅ (>= 93.79% threshold)  
**Bugbot:** ✅  
**Claude gate:** ✅  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_results.json`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_results.csv`
- `REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_run_attempts.md`

**Proof snippet(s) (PII-safe):**
```text
deterministic: order_status_rate=0.34 (68/200)
openai: order_status_rate=0.45 (90/200); openai_intent_called=199
note: ticket bucket has verified order-status rate >40%, so 0.45 is expected for this sample
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — adjusts deterministic routing and extraction logic for order-status automation.

**Failure impact:** misrouting of some order-status vs order-change/returns intents; potential baseline drift.

**Rollback plan:**
- Revert PR
- Re-run deterministic eval dataset and prod shadow report to confirm baseline restored

### 9) Reviewer + tool focus
**Please double-check:**
- Router keyword ordering and address-change guardrails.
- Order-number candidate selection for standalone digits vs date-like strings.
- Shadow report fallback logic and `--skip-openai-intent` behavior.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
