<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R3; p0_ok=true; timestamp=2026-01-29 -->

**Run ID:** `RUN_20260129_2111Z`  
**Agents:** B  
**Labels:** `risk:R3`, `gate:claude`  
**Risk:** `risk:R3`  
**Claude gate model (used):** `claude-opus-4-5-20251101` (pending — <link>)  
**Anthropic response id:** `pending — <link>`  

### 1) Summary
- Add an OpenAI intent contract for order-status routing with safe parsing and gating.
- Consolidate order-status rewrite prompts and tighten rewrite validation invariants.
- Produce PII-safe proof artifacts showing OpenAI routing + rewrite calls and final routing outcome.

### 2) Why
- **Problem / risk:** order-status automation lacked a strict LLM contract and proofable response IDs for routing/rewrites.
- **Pre-change failure mode:** LLM outputs could be ambiguous or non-JSON and still influence routing without hard evidence.
- **Why this approach:** enforce a single schema + parser, fail-closed gating, and instrument proofs for auditability.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- If OpenAI output is missing/ambiguous/low-confidence, route to support.
- Proof artifacts never contain raw emails/names/order numbers.
- OpenAI routing + rewrite response IDs are captured when calls occur.

**Non-goals (explicitly not changed):**
- No Claude gate changes or optimizations.
- No production writes or customer contact outside sandbox.

### 4) What changed
**Core changes:**
- Added order-status intent schema + parser + redaction helpers.
- Added intent/reply prompt builders and wired routing/rewrite into pipeline.
- Extended proof capture + smoke tooling with OpenAI IDs and routing excerpt fallback.

**Design decisions (why this way):**
- Fail-closed on model uncertainty to avoid automation on ambiguous intent.
- Redact ticket excerpts and include only PII-safe proof snippets.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/order_status_intent.py`
- `backend/src/richpanel_middleware/automation/order_status_prompts.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`
- `scripts/dev_e2e_smoke.py`

**Tests:**
- `backend/tests/test_order_status_intent.py`
- `backend/tests/test_order_status_context.py`
- `backend/tests/test_reply_rewrite_validation.py`
- `scripts/test_pipeline_handlers.py`
- `scripts/test_read_only_shadow_mode.py`
- `scripts/test_e2e_smoke_encoding.py`

**CI / workflows:**
- (None)

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B64/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B64/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B64/B/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B64/B/PROOF/openai_intent_rewrite_proof.json`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m pytest -q`
- `ruff check .`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --require-openai-routing --require-openai-rewrite --ticket-id <redacted> --proof-path REHYDRATION_PACK/RUNS/B64/B/PROOF/openai_intent_rewrite_proof.json --run-id b64-20260129-b11 --wait-seconds 120 --profile rp-admin-kevin`

### 7) Results & evidence
**CI:** pending — `<link>`  
**Codecov:** pending — `<direct Codecov PR link>`  
**Bugbot:** pending — `<PR link>`  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B64/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B64/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B64/B/PROOF/openai_intent_rewrite_proof.json`

**Proof snippet(s) (PII-safe):**
```text
proof_fields.openai_routing_response_id=chatcmpl-D3Tjmr5Dn1ET5Sb9u28wEraHXGQN0
proof_fields.openai_rewrite_response_id=chatcmpl-D3TjpufE3zqkMoXSESgNootEXg4th
proof_fields.final_route=order_status_automation
proof_fields.routing_ticket_excerpt_redacted=Where is my order? Please share the tracking update.
```

### 8) Risk & rollback
**Risk rationale:** `risk:R3` — changes routing + reply automation behavior and proof instrumentation.

**Failure impact:** misrouted tickets or unsafe automation if intent gating is wrong.

**Rollback plan:**
- Revert PR.
- Re-run dev_e2e_smoke proof to confirm routing + rewrite still operate under previous behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- Order-status intent gating behavior and safe failures.
- Rewrite validation invariant ordering and fallback handling.
- Proof fields include response IDs and redacted excerpt.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
- Legacy Claude/utility scripts excluded from lint.
