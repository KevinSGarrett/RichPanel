# Examples: Strong PR Titles + Descriptions

These examples are designed to score **≥95** using:
- 07_PR_TITLE_SCORING_RUBRIC.md (title)
- 03_PR_DESCRIPTION_SCORING_RUBRIC.md (body)
- and pass the minimum gate in 08.

Use these as “known-good patterns” for Cursor agents.

---

## Example 1 — Runtime behavior change (risk:R2)

### Title
`B48: Capture OpenAI evidence in GPT-5 order-status proofs (risk:R2)`

### Body (example)
```html
<!-- PR_QUALITY: title_score=98/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-01-20 -->
```

**Run ID:** `RUN_20260120_2350Z`  
**Agents:** B  
**Risk:** `risk:R2`  
**Claude gate:** Opus 4.5 (`claude-opus-4-5-20251101`)  

### 1) Summary
- Make GPT-5 request payloads model-compatible so OpenAI routing/rewrite calls succeed in order-status flow.
- Harden rewrite parsing and accept fallback as evidence (recording `error_class`) when GPT-5 returns empty/low-confidence output.
- Capture PII-safe PASS_STRONG proof artifacts for tracking/no-tracking scenarios in dev.

### 2) Why
- **Problem / risk:** Order-status proofs were failing because OpenAI evidence was missing, masking routing/rewrite behavior.
- **Pre-change failure mode:** GPT-5 requests rejected due to unsupported parameters; worker lacked permission to read `rp-mw/dev/openai/api_key`.
- **Why this approach:** Model-aware payload shaping preserves fail-closed gates and records explicit evidence without adding PII risk.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- OpenAI routing records `llm_called=true` plus `model` and `response_id` (when available).
- Rewrite attempt is recorded; fallback counts as satisfied evidence and includes `error_class`.
- Proof JSON remains PII-safe (no raw ticket bodies/emails/customer identifiers).
- No production writes (dev-only proof runs).
- Safety gates fail-closed when `safe_mode` / `automation_enabled` / `RICHPANEL_OUTBOUND_ENABLED` block calls.

**Non-goals:**
- Deterministic order-status routing logic is unchanged.
- No prod/staging deployment performed (dev only).

### 4) What changed
**Core changes:**
- `backend/src/integrations/openai/client.py`: model-aware GPT-5 payload (`max_completion_tokens`, metadata gating).
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`: hardened parsing; persist rewrite evidence; accept fallback evidence.
- `backend/src/lambda_handlers/worker/handler.py`: logs `openai_rewrite.recorded`.
- `infra/cdk/lib/richpanel-middleware-stack.ts`: grant dev worker read access to `rp-mw/dev/openai/api_key`.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/integrations/openai/client.py`
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`
- `backend/src/lambda_handlers/worker/handler.py`
- `infra/cdk/lib/richpanel-middleware-stack.ts`

**Tests:**
- `scripts/test_openai_client.py`
- `scripts/test_llm_reply_rewriter.py`
- `scripts/test_llm_routing.py`

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`

### 6) Test plan
- `python scripts/test_openai_client.py`
- `python scripts/test_llm_reply_rewriter.py`
- `python scripts/test_llm_routing.py`
- `python scripts/run_ci_checks.py --ci`

**Dev E2E proofs (redacted):**
- `python scripts/dev_e2e_smoke.py ... --ticket-number <redacted> ... --scenario order_status_tracking --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`

### 7) Results & evidence
- CI: pending — `https://github.com/<org>/<repo>/pull/<PR>/checks`
- Codecov: pending — `https://app.codecov.io/gh/<org>/<repo>/pull/<PR>`
- Bugbot: pending — `https://github.com/<org>/<repo>/pull/<PR>` (trigger via `@cursor review`)

**Proof snippet (PII-safe):**
```text
openai.routing.llm_called=true, response_id=chatcmpl-...
openai.rewrite.rewrite_attempted=true, fallback_used=true, error_class=OpenAILowConfidence
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` because this changes GPT-5 request payload construction and rewrite evidence gating in the order-status automation path.

**Rollback plan:**
- Revert this PR and redeploy dev stack.
- Re-run proof scripts to confirm the prior behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- GPT-5 payload gating and metadata handling in `OpenAIClient`
- rewrite parsing + fallback evidence recording
- dev worker secret read grant for `rp-mw/dev/openai/api_key`

**Please ignore:**
- generated registries unless CI fails
- artifacts except referenced proof JSONs

---

## Example 2 — Docs-only PR (risk:R0)

### Title
`docs(B41): Add Secrets & Environments single source of truth (risk:R0)`

### Body (example)
```html
<!-- PR_QUALITY: title_score=97/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R0; p0_ok=true; timestamp=2026-01-20 -->
```

**Risk:** `risk:R0` (docs-only)

### Summary
- Create `docs/08_Engineering/Secrets_and_Environments.md` as the canonical secrets mapping.

### Why
- Reduce confusion and prevent incorrect secret wiring across envs.

### Invariants
- No runtime behavior changed.
- No secrets/PII are included in the docs.

### Scope
- Docs:
  - `docs/08_Engineering/Secrets_and_Environments.md`

### Evidence
- CI: pending — `https://github.com/<org>/<repo>/pull/<PR>/checks`
- Codecov: N/A (docs-only)
- Bugbot: N/A

### Reviewer focus
- Double-check: tables/paths and links
- Ignore: generated registries unless CI fails

---

## Example 3 — CI/workflow gate change (risk:R2)

### Title
`B46: Harden Claude gate evidence and make it mandatory (risk:R2)`

(Body omitted for brevity; use Standard template and ensure you include:)
- invariants: “gate must be unskippable”, “comment must include response_id”
- evidence: link to Actions run that shows PASS, plus sample comment snippet
- rollback: revert workflow file changes

---

## Example 4 — High-risk behavioral change (risk:R3)

### Title
`B41: Fail-closed order-status when context missing (risk:R3)`

(Body should include:)
- explicit missing-context invariants
- negative tests proving no auto-reply
- proof that handoff tags are applied
- rollback: revert and re-run smoke proofs

