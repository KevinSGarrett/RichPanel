<!-- PR_QUALITY: title_score=100/100; body_score=99/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-19 -->

**Run ID:** `RUN_20260219_1524Z`  
**Agents:** B  
**Labels:** `risk:R2-medium`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** pending — gate not run  
**Anthropic response id:** pending — gate not run  

### 1) Summary
- Preserve deterministic delivery date windows during order-status rewrite validation.
- Expand inbound CTA denylist to block newly specified phrases.
- Tighten order-status rewrite prompt rules and align unit tests.

### 2) Why
- **Problem / risk:** Rewrites could alter or introduce delivery date ranges or add inbound CTAs.
- **Pre-change failure mode:** LLM output could shift date windows or add “message us / get back to us.”
- **Why this approach:** Add narrow deterministic date-range extraction + fail-closed validation while
  expanding phrase-based CTA guard and prompt constraints.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Non order-status flows remain unchanged (greeting/signature enforcement is order-status only).
- URL/tracking/ETA preservation validations remain intact and enforced.
- Missing/changed or unexpected delivery date windows fail closed to deterministic draft reply.

**Non-goals (explicitly not changed):**
- No AWS/CDK changes or deployments.
- No Richpanel ticket writes or outbound sends.

### 4) What changed
**Core changes:**
- Added deterministic delivery date-range extraction + canonicalization to rewrite validation.
- Extended missing/unexpected validation to include delivery date windows with new reason codes.
- Expanded inbound CTA denylist and updated order-status prompt constraints.

**Design decisions (why this way):**
- Month/day/year requirement avoids false positives and keeps validation narrow.
- Canonicalization treats dash/en-dash variants as equivalent and reduces false rejections.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/order_status_prompts.py`

**Tests:**
- `backend/tests/test_reply_rewrite_validation.py`
- `backend/tests/test_order_status_reply_personalization.py`
- `scripts/test_llm_reply_rewriter.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/_generated/*`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/*`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/run_ci_checks.py --ci`
- `pytest -q`
- `python scripts/verify_rehydration_pack.py`
- `python scripts/verify_agent_prompts_fresh.py`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- Not run (no outbound send or deployment in this agent run).

### 7) Results & evidence
**CI:** pending — link after PR  
**Codecov:** pending — link after PR  
**Bugbot:** pending — trigger via `@cursor review` after PR  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/run_ci_checks_ci.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/pytest_q.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/verify_rehydration_pack.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/verify_agent_prompts_fresh.log`
- `REHYDRATION_PACK/RUNS/RUN_20260219_1524Z/B/evidence/prompt_fingerprint.log`

**Proof snippet(s) (PII-safe):**
```text
[OK] CI-equivalent checks passed.
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — affects order-status rewrite validation and prompt constraints.

**Failure impact:** Incorrect rewriter acceptance/rejection or CTA leakage in order-status replies.

**Rollback plan:**
- Revert PR
- Re-run `python scripts/run_ci_checks.py --ci` and `pytest -q` to confirm

### 9) Reviewer + tool focus
**Please double-check:**
- Date-window extraction/canonicalization and missing/unexpected reason selection
- CTA denylist coverage and prompt wording alignment with spec

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
