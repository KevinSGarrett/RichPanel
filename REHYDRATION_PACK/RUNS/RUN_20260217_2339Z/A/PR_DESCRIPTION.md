<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R3; p0_ok=true; timestamp=2026-02-17 -->

**Run ID:** RUN_20260217_2339Z  
**Agents:** A (B/C inactive artifacts only)  
**Labels:** 
isk:R3-high, gate:claude  
**Risk:** 
isk:R3-high  
**Claude gate model (used):** claude-opus-4-5-20251101  
**Anthropic response id:** pending — https://github.com/KevinSGarrett/RichPanel/pull/259/checks  

### 1) Summary
- Add customer first-name + sanitized message excerpt context to order-status rewrite prompt.
- Enforce deterministic greeting/signature wrapping after rewrite.
- Add rewrite temperature env support with conservative clamp and tests.

### 2) Why
- **Problem / risk:** LLM rewrite lacked customer-message context and could miss greeting/signature consistency.
- **Pre-change failure mode:** Prompts could not mirror customer concern, and greetings/signatures were not deterministic.
- **Why this approach:** Keep rewrite validations intact, add explicit context, and enforce wrappers deterministically in pipeline.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Reply rewrite still preserves URLs/tracking numbers/ETA windows (validations unchanged).
- Reply body never includes greeting/signature from the model; pipeline adds them deterministically.
- Greeting format is always Hi <FirstName>, or Hi there, with a blank line after.
- Signature always ends with exactly:
  - Holly
  - Scentiment Customer Support
- No outbound sends or ticket updates triggered by these changes alone.

**Non-goals (explicitly not changed):**
- No changes to routing logic or outbound gating behavior.
- No changes to rewrite confidence thresholds or validation rules.

### 4) What changed
**Core changes:**
- Added explicit first-name extraction + sanitized/truncated customer message excerpt in pipeline context.
- Expanded REPLY_SYSTEM_PROMPT with brand voice, tone mapping, and “no AI/bot/template” rules.
- Added deterministic greeting/signature enforcement after rewrite.
- Added OPENAI_REPLY_REWRITE_TEMPERATURE with conservative clamp.

**Design decisions (why this way):**
- Extract first name only from explicit fields to avoid guessing.
- Limit excerpt to 400 chars to keep prompts bounded and PII-redacted.
- Clamp temperature to 0.7 for conservative rewrite behavior.

### 5) Scope / files touched
**Runtime code:**
- ackend/src/richpanel_middleware/automation/pipeline.py
- ackend/src/richpanel_middleware/automation/order_status_prompts.py
- ackend/src/richpanel_middleware/automation/llm_reply_rewriter.py

**Tests:**
- ackend/tests/test_order_status_reply_personalization.py

**CI / workflows:**
- None

**Docs / artifacts:**
- docs/00_Project_Admin/Progress_Log.md
- docs/_generated/*
- REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_REPORT.md
- REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/TEST_MATRIX.md
- REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_SUMMARY.md

### 6) Test plan
**Local / CI-equivalent:**
- python scripts/run_ci_checks.py --ci
- $env:AWS_REGION="us-east-2"; us-east-2="us-east-2"; pytest -q

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- None (not required for this change set)

### 7) Results & evidence
**CI:** pending — https://github.com/KevinSGarrett/RichPanel/pull/259/checks  
**Codecov:** pending — https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/259  
**Bugbot:** pending — https://github.com/KevinSGarrett/RichPanel/pull/259 (trigger via @cursor review)  

**Artifacts / proof:**
- REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_REPORT.md
- REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/TEST_MATRIX.md
- REHYDRATION_PACK/RUNS/RUN_20260217_2339Z/A/RUN_SUMMARY.md

**Proof snippet(s) (PII-safe):**
```text
[OK] CI-equivalent checks passed.
1559 passed, 18 subtests passed in 228.09s (0:03:48)
```

### 8) Risk & rollback
**Risk rationale:** `risk:R3-high` — customer-facing automation prompt + pipeline changes.

**Failure impact:** Incorrect greeting/signature formatting or missing tone mirroring in customer replies.

**Rollback plan:**
- Revert PR
- Re-run `python scripts/run_ci_checks.py --ci` and `pytest -q` to confirm rollback

### 9) Reviewer + tool focus
**Please double-check:**
- Greeting/signature enforcement logic in pipeline.py.
- Prompt changes ensure no AI/bot/template mentions and no greeting/signature in body.
- Rewrite temperature env parsing/clamping does not alter validations.
- New tests cover excerpt sanitization and greeting/signature idempotency.

**Please ignore:**
- Generated registries unless CI fails.
- Rehydration pack artifacts except referenced proof files.
