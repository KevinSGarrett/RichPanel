# Examples of Strong PR Descriptions

These examples are written to score **≥95/100** using the rubric.

---

## Example A — Runtime safety gate (risk:R3)

**Run ID:** `RUN_20260118_1717Z`  
**Agents:** B  
**Risk:** `risk:R3`  
**Claude gate:** Opus 4.5  

### Summary
- Fail-closed: suppress order-status auto-reply when required order context is missing.
- Route suppressed cases to Email Support Team with explicit diagnostic tags.
- Add unit tests proving missing-context paths never auto-close.

### Why
- **Problem / risk:** missing order context could cause incorrect ETA/tracking claims and premature ticket closure.
- **Pre-change failure mode:** deterministic fallback could imply “we have order X” even when `order_id`/`created_at` were missing.
- **Why this approach:** fail-closed routing to a human is safer than any auto-response under uncertainty.

### Expected behavior & invariants
**Must hold (invariants):**
- No auto-reply if `order_id` OR `created_at` is missing.
- No auto-reply if both tracking and shipping-method bucket are missing.
- When suppressed, ticket is tagged for support routing (`route-email-support-team`) and diagnostic tags are added.
- Fallback wording must never claim an order exists when `order_id` is unknown.

**Non-goals:**
- Does not change the happy-path order-status behavior when context is complete.

### What changed
- Added `_missing_order_context()` validation and enforced it in `pipeline.plan_actions()`.
- Updated no-tracking reply copy to avoid false confidence when `order_id` is unknown.

### Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`

**Tests:**
- `backend/tests/test_order_status_context.py`
- `scripts/test_pipeline_handlers.py`

**Docs:**
- `docs/05_FAQ_Automation/Order_Status_Automation.md`

### Test plan
- `python scripts/run_ci_checks.py --ci`
- `python -m pytest backend/tests/test_order_status_context.py -q`

### Results & evidence
**CI:** <actions link>  
**Codecov:** <codecov link>  
**Bugbot:** <bugbot link>  

**Artifacts:**
- `REHYDRATION_PACK/RUNS/RUN_20260118_1717Z/B/TEST_EVIDENCE.md`

### Risk & rollback
**Risk rationale:** R3 because this changes core automation decision logic.

**Rollback plan:** revert this PR. No data migrations.

### Reviewer + tool focus
**Please double-check:**
- gating logic in `pipeline.plan_actions()` matches invariants above
- tests cover all missing-field permutations

**Please ignore:**
- generated doc registries unless CI fails

---

## Example B — Logging privacy gate (risk:R2)

**Run ID:** `RUN_20260115_1200Z`  
**Agents:** A  
**Risk:** `risk:R2`  
**Claude gate:** Opus 4.5  

### Summary
- Make OpenAI response excerpt logging opt-in behind `OPENAI_LOG_RESPONSE_EXCERPT` (default OFF).
- Add config helper and tests proving excerpt is absent unless enabled.

### Why
- Logging excerpts risks accidental PII exposure.
- Default-off reduces privacy risk while preserving debugging capability when explicitly enabled.

### Expected behavior & invariants
**Must hold:**
- Default behavior logs no response excerpt.
- When enabled, excerpt is truncated to 200 chars.
- No raw request bodies are logged.

**Non-goals:**
- No changes to API request behavior.

### Test plan
- `python scripts/run_ci_checks.py --ci`
- `python -m pytest scripts/test_openai_client.py -q`

### Evidence
- CI: <actions link>
- Codecov: <codecov link>
- Bugbot: <bugbot link>

---

## Example C — Docs-only PR (risk:R0)

**Risk:** `risk:R0` (docs only)

### Summary
- Add canonical documentation for secrets and environment configuration.

### Why
- Reduce operational mistakes by consolidating secret paths and rotation guidance.

### Invariants
- No runtime code changes.
- No production behavior changes.

### Evidence
- Doc hygiene CI: <actions link>
- Registry regen: `docs/_generated/doc_registry.json`

