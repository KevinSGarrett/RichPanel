<!-- PR_QUALITY: title_score=96/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R3; p0_ok=true; timestamp=2026-01-25 -->

**Run ID:** `RUN_20260125_0130Z`  
**Agents:** A  
**Labels:** `risk:R3`, `gate:claude`  
**Risk:** `risk:R3`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_017pVP7CojYpLVkj5dQLoxJJ`  

### 1) Summary
- Deliver email-channel outbound order-status replies through Richpanel `/send-message` with operator author resolution and failure routing tags.
- Preserve the non-email comment+close path while adding deterministic path tags for audit clarity.
- Enforce LLM routing confidence threshold even when `force_primary` is set.

### 2) Why
- **Problem / risk:** Email-channel order-status replies posted as middleware comments can be hidden in UI and never delivered to customers.
- **Pre-change failure mode:** Tickets closed with middleware comments show `message_count_delta` in backend proofs but do not generate customer-visible email replies.
- **Why this approach:** `/send-message` is the Richpanel operator reply path; author resolution plus explicit failure routing prevents silent closes while keeping non-email behavior unchanged.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Email-channel tickets use `/v1/tickets/{id}/send-message` with a resolved `author_id` before any close attempt.
- Non-email/unknown channels continue using the existing middleware comment + close flow.
- No outbound writes occur when `safe_mode`, `automation_enabled`, `allow_network`, or `outbound_enabled` gates block execution.
- `force_primary` does not bypass the configured LLM confidence threshold.
- No PII (emails/names) is logged for author selection; only strategy + short id hash.

**Non-goals (explicitly not changed):**
- No changes to draft reply content or order-status prompt/rewrite logic.
- No changes to non-order-status automation paths or other ticket intents.
- No new Richpanel API clients or auth changes beyond existing executor usage.

### 4) What changed
**Core changes:**
- `execute_order_status_reply()` now selects `/send-message` for email-channel tickets and closes via safe update candidates without a middleware comment.
- Author resolution prefers `RICHPANEL_BOT_AUTHOR_ID`, then `GET /v1/users` with agent/operator role matching.
- Added deterministic path tags (`mw-outbound-path-send-message` vs `mw-outbound-path-comment`) and explicit failure routing tags.
- Apply loop-prevention tags even when send-message succeeds but ticket close fails, routing to support with explicit reason tags.
- `compute_dual_routing()` always uses `get_confidence_threshold()` even with `force_primary`.
- Added sandbox proof flags in `dev_e2e_smoke.py` for operator replies and `/send-message` tags, plus a proof template artifact.

**Design decisions (why this way):**
- Use the existing executor and safe update-candidate strategy to avoid introducing new write semantics.
- Route failures to support with explicit tags rather than silently closing when `/send-message` fails.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/llm_routing.py`

**Tests:**
- `scripts/test_pipeline_handlers.py`
- `scripts/test_llm_routing.py`
- `scripts/test_e2e_smoke_encoding.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/03_Richpanel_Integration/Outbound_Reply_Paths.md`
- `REHYDRATION_PACK/RUNS/B58/A/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B58/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B58/A/CI_RUN_OUTPUT.txt`
- `REHYDRATION_PACK/RUNS/B58/A/PROOF/order_status_email_sandbox_proof_template.json`

**Hotspots:**
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/llm_routing.py`
- `scripts/test_pipeline_handlers.py`
- `scripts/dev_e2e_smoke.py`
- `docs/03_Richpanel_Integration/Outbound_Reply_Paths.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/run_ci_checks.py --ci`
- `python scripts/test_pipeline_handlers.py`
- `python scripts/test_llm_routing.py`
- `python scripts/test_e2e_smoke_encoding.py`

**E2E / proof runs (redacted):**
- `python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --scenario order_status --ticket-number <redacted> --no-require-outbound --require-openai-routing --require-openai-rewrite --require-send-message --require-operator-reply --followup --run-id B58-SANDBOX-20260125160800 --proof-path REHYDRATION_PACK/RUNS/B58/A/PROOF/order_status_email_sandbox_proof.json`

### 7) Results & evidence
**CI:** pass — `https://github.com/KevinSGarrett/RichPanel/pull/183/checks`  
**Codecov:** pass — `https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/183`  
**Bugbot:** pass — `https://github.com/KevinSGarrett/RichPanel/pull/183`  
**Claude gate:** pass — `https://github.com/KevinSGarrett/RichPanel/actions/runs/21339795015/job/61417362979`  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B58/A/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B58/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B58/A/CI_RUN_OUTPUT.txt`
- `REHYDRATION_PACK/RUNS/B58/A/PROOF/order_status_email_sandbox_proof.json`

**Proof snippet(s) (PII-safe):**
```text
paths: ['/v1/tickets/t-email', '/v1/tickets/t-email/send-message', '/v1/tickets/t-email', '/v1/tickets/t-email', '/v1/tickets/t-email/add-tags']
[OK] CI-equivalent checks passed.
[RESULT] classification=PASS_STRONG; status=PASS; failure_reason=none
```

### 8) Risk & rollback
**Risk rationale:** `risk:R3` — outbound email delivery correctness; failures directly affect customer communication.

**Failure impact:** Email replies could be missing or tickets could close without customer-visible responses.

**Rollback plan:**
- Revert this PR.
- Redeploy the previous build.
- Re-run `python scripts/test_pipeline_handlers.py` and confirm the outbound path proof in `REHYDRATION_PACK/RUNS/B58/A/EVIDENCE.md`.

### 9) Reviewer + tool focus
**Please double-check:**
- Email-channel detection and author resolution logic in `execute_order_status_reply()`.
- `/send-message` failure handling (no close, route to support with explicit tags).
- Close path avoids middleware comment for email replies.
- `force_primary` threshold behavior in `compute_dual_routing()`.

**Please ignore:**
- Generated registries in `docs/_generated/*` unless CI flags them.
- Rehydration run artifacts outside `REHYDRATION_PACK/RUNS/B58/A/*`.
