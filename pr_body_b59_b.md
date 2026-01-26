<!-- PR_QUALITY: title_score=96/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-01-26 -->

**Run ID:** `B59-SANDBOX-AUTOTICKET-20260126-1254Z`  
**Agents:** B  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01B4LrGLzPceQhQLQcDhaGSL`  
**Anthropic request id:** `req_011CXWWMGT5mPhnX9E4poA6y`  

### 1) Summary
- Add sandbox auto-ticket creation so E2E order-status proofs no longer depend on manually sourced ticket numbers.
- Integrate `--create-ticket` flow into `dev_e2e_smoke.py` with PII-safe artifacts for created tickets.
- Produce a PASS_STRONG auto-ticket proof showing operator reply, send-message path, and follow-up routing.

### 2) Why
- **Problem / risk:** Manual ticket sourcing makes sandbox E2E runs brittle and slows iteration.
- **Pre-change failure mode:** Proof runs fail or stall waiting on fresh ticket numbers.
- **Why this approach:** Create a fresh sandbox email ticket via Richpanel API and immediately run the scenario against it.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Auto-ticket flow creates a sandbox email ticket and uses it for the E2E run.
- Proof JSON shows OpenAI routing + rewrite used, operator reply evidence, and send-message path tags.
- Follow-up is routed to support without a second auto-reply.
- Artifacts remain PII-safe (no raw emails/ticket numbers).

**Non-goals (explicitly not changed):**
- No backend workflow changes; scripts-only.
- No changes to order-status reply content or pipeline logic.

### 4) What changed
**Core changes:**
- Added `scripts/create_sandbox_email_ticket.py` for sandbox email ticket creation (PII-safe output).
- Added `--create-ticket` and ticket input flags to `scripts/dev_e2e_smoke.py`.
- Updated proof redaction coverage for new CLI inputs.

**Design decisions (why this way):**
- Reuse existing Richpanel client + Secrets Manager flow for consistency with dev_e2e_smoke.

### 5) Scope / files touched
**Runtime code:**
- `scripts/create_sandbox_email_ticket.py`
- `scripts/dev_e2e_smoke.py`

**Tests:**
- `scripts/test_e2e_smoke_encoding.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B59/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B59/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B59/B/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B59/B/PROOF/created_ticket.json`
- `REHYDRATION_PACK/RUNS/B59/B/PROOF/order_status_operator_reply_followup_proof_autoticket.json`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/test_e2e_smoke_encoding.py`

**E2E / proof runs (redacted):**
- `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --require-openai-routing --require-openai-rewrite --require-outbound --require-operator-reply --require-send-message-path --followup --run-id B59-SANDBOX-AUTOTICKET-20260126-1254Z --proof-path REHYDRATION_PACK/RUNS/B59/B/PROOF/order_status_operator_reply_followup_proof_autoticket.json --create-ticket-proof-path REHYDRATION_PACK/RUNS/B59/B/PROOF/created_ticket.json`

### 7) Results & evidence
**CI:** pass — `https://github.com/KevinSGarrett/RichPanel/actions/runs/21370196017/job/61512445227`  
**Codecov:** fail — `https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/187`  
**Bugbot:** pass — `https://cursor.com`  
**Claude gate:** pass — `https://github.com/KevinSGarrett/RichPanel/actions/runs/21370202358/job/61512482149`  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B59/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B59/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B59/B/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B59/B/PROOF/created_ticket.json`
- `REHYDRATION_PACK/RUNS/B59/B/PROOF/order_status_operator_reply_followup_proof_autoticket.json`

**Proof snippet(s) (PII-safe):**
```text
proof_fields.openai_routing_used: true
proof_fields.openai_rewrite_used: true
proof_fields.latest_comment_is_operator: true
proof_fields.send_message_path_confirmed: true
proof_fields.closed_after: true
followup.routed_to_support: true
followup.reply_sent: false
result.classification: PASS_STRONG
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — new automation path for sandbox proof runs; scripts-only changes.

**Failure impact:** Proof runs could fail to create tickets or mis-attribute ticket references.

**Rollback plan:**
- Revert PR.
- Run the pre-existing manual-ticket smoke command to confirm baseline behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- Auto-ticket uses ticket id for lookup and ticket number for payload when available.
- PII redaction covers new ticket input flags and proof artifacts.
- Proof JSON evidence matches operator reply + send-message path requirements.

**Please ignore:**
- Rehydration pack artifacts outside `REHYDRATION_PACK/RUNS/B59/B/*`.
