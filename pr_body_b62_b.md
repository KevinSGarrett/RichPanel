<!-- PR_QUALITY: title_score=96/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R3; p0_ok=true; timestamp=2026-01-28 -->

**Run ID:** `b62-20260128-b`  
**Agents:** B  
**Labels:** `risk:R3`, `gate:claude`  
**Risk:** `risk:R3`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01QLAztiiKBABLxqnbcV5bv2`  
**Anthropic request id:** `req_011CXZHWftEi1sSA9cc7tnu6`  
**Anthropic usage:** input_tokens=24406; output_tokens=441; cache_creation_input_tokens=0; cache_read_input_tokens=0; service_tier=standard

### 1) Summary
- Made outbound reply path selection channel-aware to avoid mis-sending on non-email tickets.
- Enforced email `/send-message` with operator-comment verification before close/tagging.
- Applied allowlist gating across outbound paths and cached bot author resolution.
- Added unit coverage, dev smoke proof, and reply-path documentation.

### 2) Why
- **Problem / risk:** outbound replies could be routed by metadata but not actually delivered, especially for email vs non-email channels.
- **Pre-change failure mode:** email tickets could fall back to comment updates or close without confirming the operator reply was created.
- **Why this approach:** prefer deterministic channel detection + verify operator replies to prevent false positives and fail closed when uncertain.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Email-channel tickets send via `PUT /v1/tickets/{id}/send-message` and verify `is_operator=true` before closing.
- Non-email channels never call `/send-message`.
- Allowlist/safety gating blocks outbound for any channel when not permitted.
- Missing bot author id blocks email outbound (no comment fallback).
- Proof artifacts remain PII-safe (no raw emails, ticket IDs, or order numbers).

**Non-goals (explicitly not changed):**
- Routing intent logic and LLM routing selection.
- Richpanel client safety gating outside order-status replies.

### 4) What changed
**Core changes:**
- Added channel detection helpers to select the outbound path deterministically.
- Added operator-comment verification after `/send-message` and before close.
- Applied allowlist gating to all outbound reply paths.
- Cached bot author id resolution when falling back to `/v1/users`.

**Design decisions (why this way):**
- Prefer envelope/ticket metadata for channel to avoid extra fetches; fall back to ticket GET when missing.
- Operator verification relies on `is_operator` flags only, avoiding reply body handling.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `scripts/create_sandbox_chat_ticket.py`

**Tests:**
- `scripts/test_pipeline_handlers.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/08_Engineering/Richpanel_Reply_Paths.md`
- `REHYDRATION_PACK/RUNS/B62/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B62/B/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B62/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_proof.json`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/unit_test_output.txt`

**Hot files:**
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `scripts/test_pipeline_handlers.py`
- `scripts/create_sandbox_chat_ticket.py`
- `docs/08_Engineering/Richpanel_Reply_Paths.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/test_pipeline_handlers.py`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-outbound --require-send-message-path --require-operator-reply --create-ticket --create-ticket-proof-path REHYDRATION_PACK/RUNS/B62/B/PROOF/created_ticket.json --proof-path REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_proof.json --profile rp-admin-kevin --run-id b62-20260128-b`
- `python scripts/create_sandbox_chat_ticket.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --proof-path REHYDRATION_PACK/RUNS/B62/B/PROOF/created_chat_ticket.json --emit-ticket-ref --profile rp-admin-kevin --channel chat`

### 7) Results & evidence
**CI:** pending - https://github.com/KevinSGarrett/RichPanel/actions  
**Codecov:** pending - https://codecov.io/gh/KevinSGarrett/RichPanel  
**Bugbot:** pending - https://cursor.com  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_proof.json`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_output.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/unit_test_output.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/created_ticket.json`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/create_chat_ticket_error.txt`

**Proof snippet(s) (PII-safe):**
```text
- ticket_channel: email
- send_message_path_confirmed: true
- latest_comment_is_operator: true
- closed_after: true
```

Non-email limitation (PII-safe):
```text
- non-email ticket creation rejected: ticket.via.channel invalid for chat
- non-email path validated via unit tests
```

### 8) Risk & rollback
**Risk rationale:** `risk:R3` - changes govern outbound customer communication and ticket lifecycle handling.

**Failure impact:** outbound replies could be blocked or incorrectly routed for email vs non-email channels.

**Rollback plan:**
- Revert PR.
- Re-deploy worker Lambda.
- Re-run the dev smoke proof above to confirm previous behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- Channel detection + allowlist gating order in `execute_order_status_reply`.
- Operator-comment verification behavior on the `/send-message` path.
- Author id caching and email-only send-message enforcement.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
