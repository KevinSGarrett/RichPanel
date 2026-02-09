```html
<!-- PR_QUALITY: title_score=96/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-09 -->
```

**Run ID:** `B74_A_20260209_0028Z`  
**Agents:** A  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_0134dwePqPTHYTJXmVyDow3j`  

### 1) Summary
- Add Secrets Manager bot agent id resolution and enforce email-only `/send-message`.
- Preserve fail-closed safety gates, read-only guards, and follow-up routing to support.
- Extend proof runner fields and tests for operator-reply evidence and decision logic.

### 2) Why
- **Problem / risk:** Middleware comments were not guaranteed to send customer email; bot agent id resolution depended on `/v1/users`.
- **Pre-change failure mode:** Email tickets could fall back to middleware comments or use noisy user lookup.
- **Why this approach:** Secrets Manager bot id + explicit channel gating keeps outbound deterministic and safe.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- `/send-message` is used only when `channel_detected == email`, bot agent id is present, and outbound gates are open.
- Read-only and outbound-disabled guards always block sends and remain fail-closed.
- Proof artifacts remain PII-safe (no raw emails, names, order numbers, tracking links).

**Non-goals (explicitly not changed):**
- No PROD outbound enablement or Shopify order creation.
- No non-order-status automation changes.

### 4) What changed
**Core changes:**
- Added bot agent id resolution via `RICHPANEL_BOT_AGENT_ID` or Secrets Manager (`rp-mw/{env}/richpanel/bot_agent_id`).
- Enforced email-only `/send-message` path with channel detection + read-only guard reporting.
- Extended dev proof runner fields and unit tests for operator reply evidence and follow-up routing.

**Design decisions (why this way):**
- Avoid `/v1/users` lookup to prevent rate-limit noise.
- Keep outbound decisions fail-closed with explicit diagnostics for proofing.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/lambda_handlers/worker/handler.py`

**Tests:**
- `scripts/test_order_status_send_message.py`
- `scripts/test_pipeline_handlers.py`
- `scripts/test_e2e_smoke_encoding.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/08_Engineering/Richpanel_Reply_Paths.md`
- `REHYDRATION_PACK/RUNS/B74/A/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B74/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B74/A/PROOF/dev_sandbox_e2e_operator_reply.json`

### 6) Test plan
**Local / CI-equivalent:**
- Not run (local verification pending).

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --ticket-number <redacted> --require-outbound --require-operator-reply --followup --run-id B74_A_20260209_0028Z --proof-path REHYDRATION_PACK/RUNS/B74/A/PROOF/dev_sandbox_e2e_operator_reply.json`

### 7) Results & evidence
**CI:** pending — https://github.com/KevinSGarrett/RichPanel/pull/234/checks  
**Codecov:** pending — https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/234  
**Bugbot:** pending — https://github.com/KevinSGarrett/RichPanel/pull/234 (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B74/A/PROOF/dev_sandbox_e2e_operator_reply.json`

**Proof snippet(s) (PII-safe):**
```text
send_message_endpoint_used=true
send_message_status_code=200
is_operator_reply=true
channel_detected=email
bot_agent_id_source=secrets_manager
read_only_guard_active=false
followup_reply_sent=false
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — touches outbound reply path but remains fully gated and email-only.

**Failure impact:** Incorrect gating could block replies or send via wrong path.

**Rollback plan:**
- Revert PR
- Redeploy middleware stack
- Re-run `scripts/dev_e2e_smoke.py` proof to confirm rollback

### 9) Reviewer + tool focus
**Please double-check:**
- Email-only `/send-message` gating and bot id missing fallback behavior.
- Read-only guard enforcement and absence of `/v1/users` lookup.

**Please ignore:**
- Rehydration pack artifacts except the referenced proof files.
