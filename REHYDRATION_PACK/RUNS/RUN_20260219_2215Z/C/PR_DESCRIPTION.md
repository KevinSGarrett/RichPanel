# PR Description

```html
<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-19 -->
```

**Run ID:** `RUN_20260219_2215Z`  
**Agents:** C  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-sonnet-4-5-20250801` (pending run)  
**Anthropic response id:** `pending — PR gate`

### 1) Summary
- Reformat deterministic order-status drafts into short paragraphs for readability.
- Strip shipping-window parentheticals from shipping_method context and make CTA guard non-destructive.
- Replace order-status rewrite prompt with stricter formatting/tone guidance; update tests/registries.

### 2) Why
- **Problem / risk:** Drafts are clause-heavy and look robotic when rewrite falls back or preserves phrasing.
- **Pre-change failure mode:** Timeline facts appear as a single run-on sentence; CTA guard reverts the entire rewrite.
- **Why this approach:** Fix the deterministic draft source and guard behavior while keeping validation strict and fail-closed.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Greeting/signature remain deterministic and unchanged.
- URLs/tracking numbers/ETA windows/date ranges preserved; validation remains strict.
- No inbound-encouraging CTA phrases appear in final replies.

**Non-goals (explicitly not changed):**
- Routing/intent logic.
- Validation looseness or safety gating.
- OpenAI model selection/config defaults.

### 4) What changed
**Core changes:**
- Rebuilt no-tracking timeline and tracking-present drafts into short paragraphs.
- Stripped shipping window from shipping_method context.
- CTA guard now removes CTA sentences instead of reverting the entire rewrite.
- Replaced order-status rewrite prompt per Auto_Reply_Upgrade_003.

**Design decisions (why this way):**
- Fix readability at the draft source so fallbacks remain acceptable.
- Preserve safety rules by only removing CTA sentences, not loosening validation.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/order_status_prompts.py`

**Tests:**
- `backend/tests/test_delivery_estimate_fallback.py`
- `backend/tests/test_order_status_reply_personalization.py`
- `backend/tests/test_tracking_link_generation.py`
- `scripts/test_delivery_estimate.py`
- `scripts/test_e2e_smoke_encoding.py`
- `scripts/test_live_readonly_shadow_eval.py`
- `scripts/test_pipeline_handlers.py`

**CI / workflows:**
- None.

**Docs / artifacts:**
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/_generated/*`
- `REHYDRATION_PACK/RUNS/RUN_20260219_2215Z/C/RUN_REPORT.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/run_ci_checks.py --ci`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- Not run (changes validated via deterministic/unit tests).

### 7) Results & evidence
**CI:** pending — `<PR link>`  
**Codecov:** pending — `<Codecov PR link>`  
**Bugbot:** pending — `<PR link>`  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260219_2215Z/C/evidence/run_ci_checks_ci.log`

**Proof snippet(s) (PII-safe):**
```text
[OK] CI-equivalent checks passed.
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — customer-facing reply phrasing and formatting changes.  

**Failure impact:** Replies may read awkwardly or omit desired phrasing; safety validation still fail-closed.  

**Rollback plan:**
- Revert PR.
- Redeploy previous stack / app version if already deployed.
- Re-run `python scripts/run_ci_checks.py --ci` to confirm rollback state.

### 9) Reviewer + tool focus
**Please double-check:**
- Draft formatting is now multi-paragraph and not clause-heavy.
- CTA guard strips CTA sentences without discarding the rewrite.

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
