<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R3; p0_ok=true; timestamp=2026-01-28 -->

**Run ID:** `b62-20260128-b2`  
**Agents:** B  
**Labels:** `risk:R3`, `gate:claude`  
**Risk:** `risk:R3`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01LpAGJVjW8mNNcBsDjMbmc1`  
**Anthropic request id:** `req_011CXZqqT9H5qhabqyr87esN`  
**Anthropic usage:** input_tokens=23857; output_tokens=600; cache_creation_input_tokens=0; cache_read_input_tokens=0; service_tier=standard

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
- Unknown channel is treated as non-email (comment path only).
- Missing bot author id blocks email outbound (no comment fallback).
- Proof artifacts remain PII-safe (no raw emails, ticket IDs, or order numbers).

**Non-goals (explicitly not changed):**
- Routing intent logic and LLM routing selection.
- Richpanel client safety gating outside order-status replies.

### 4) What changed
**Core changes:**
- Added channel detection helpers to select the outbound path deterministically.
- Added operator-comment verification after `/send-message` and before close.
- Added loop-prevention tags when operator verification fails after `/send-message`.
- Normalized comment timestamps to UTC to prevent mixed timezone comparison crashes.
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
- `python scripts/test_e2e_smoke_encoding.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/08_Engineering/Richpanel_Reply_Paths.md`
- `docs/REGISTRY.md`
- `docs/_generated/doc_outline.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_registry.json`
- `docs/_generated/heading_index.json`
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
- `python scripts/run_ci_checks.py --ci`
- `python scripts/test_pipeline_handlers.py`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-outbound --require-send-message-path --require-operator-reply --create-ticket --create-ticket-proof-path REHYDRATION_PACK/RUNS/B62/B/PROOF/created_ticket.json --proof-path REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_proof.json --profile rp-admin-kevin --run-id b62-20260128-b2`
- `python scripts/create_sandbox_chat_ticket.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --proof-path REHYDRATION_PACK/RUNS/B62/B/PROOF/created_chat_ticket.json --emit-ticket-ref --profile rp-admin-kevin --channel chat`

### 7) Results & evidence
**CI:** pending - https://github.com/KevinSGarrett/RichPanel/pull/200/checks  
**Codecov:** pending - https://codecov.io/gh/KevinSGarrett/RichPanel/pull/200  
**Bugbot:** pending - https://github.com/KevinSGarrett/RichPanel/pull/200 (trigger via `@cursor review`)  
**Claude gate:** https://github.com/KevinSGarrett/RichPanel/actions/runs/21439788645  

Local CI-equivalent status: `python scripts/run_ci_checks.py --ci` failed due to regenerated docs/registry changes already present; see `REHYDRATION_PACK/RUNS/B62/B/PROOF/run_ci_checks_output.txt`.

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_proof.json`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_output.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/unit_test_output.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/test_e2e_smoke_encoding_output.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/run_ci_checks_output.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/created_ticket.json`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/create_chat_ticket_error.txt`
- `REHYDRATION_PACK/RUNS/B62/B/PROOF/claude_gate_audit.json`

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
- Generated docs registries in `docs/_generated/*` unless CI fails.
