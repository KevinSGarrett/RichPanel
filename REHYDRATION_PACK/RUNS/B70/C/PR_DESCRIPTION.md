```html
<!-- PR_QUALITY: title_score=95/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R1; p0_ok=true; timestamp=2026-02-04 -->
```

**Run ID:** `B70-C-20260204-0007`  
**Agents:** C  
**Labels:** `risk:R1`, `gate:claude`  
**Risk:** `risk:R1`  
**Claude gate model (used):** pending — not run  
**Anthropic response id:** pending — not run  

### 1) Summary
- Adds explicit proof field for `/send-message` usage in DEV E2E smoke output.
- Captures DEV sandbox E2E proof with operator-visible reply and auto-close.
- Produces PII-safe artifacts for order-status automation with Shopify read-only lookup.

### 2) Why
- **Problem / risk:** Prior proof gaps didn’t explicitly show `/send-message` usage or operator visibility.
- **Pre-change failure mode:** Proof JSON lacked a direct `send_message_endpoint_used` field.
- **Why this approach:** Alias existing `send_message_used` to an explicit `send_message_endpoint_used` field for clear evidence without changing behavior.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- DEV Richpanel remains writable; PROD remains untouched.
- Proof artifacts are PII-safe (ticket/order numbers redacted).
- Outbound replies use `/send-message` and are operator-visible (`is_operator: true`).

**Non-goals (explicitly not changed):**
- No changes to production configuration or secrets.
- No changes to order lookup logic beyond proof instrumentation.
- No changes to workflow/CI configuration.

### 4) What changed
**Core changes:**
- Added `send_message_endpoint_used` proof field to DEV E2E smoke output.
- Added test assertions for the new proof field.

**Design decisions (why this way):**
- Use a simple alias to avoid behavioral changes while providing explicit evidence.

### 5) Scope / files touched
**Runtime code:**
- `scripts/dev_e2e_smoke.py`

**Tests:**
- `scripts/test_e2e_smoke_encoding.py`

**CI / workflows:**
- None.

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B70/C/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B70/C/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B70/C/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_summary.json`
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run7.json`
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_created_ticket_run7.json`

### 6) Test plan
**Local / CI-equivalent:**
- Not run (only proof run below).

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --create-ticket --order-number <redacted> --require-openai-routing --require-openai-rewrite --require-order-match-by-number --require-outbound --require-send-message --require-send-message-used --require-operator-reply --proof-path REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run7.json --create-ticket-proof-path REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_created_ticket_run7.json --run-id B70-C-20260204-0007 --wait-seconds 120 --profile rp-admin-dev`

### 7) Results & evidence
**CI:** pending — not run  
**Codecov:** pending — not run  
**Bugbot:** pending — not run  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_summary.json`
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run7.json`

**Proof snippet(s) (PII-safe):**
```text
send_message_endpoint_used: true
send_message_status_code: 200
latest_comment_is_operator: true
send_message_author_matches_bot_agent: true
order_match_method: order_number
order_match_by_number: true
closed_after: true
```

### 8) Risk & rollback
**Risk rationale:** `risk:R1` — proof instrumentation only; no runtime behavior changes.  

**Failure impact:** Proof fields could be missing, reducing evidence quality for E2E verification.  

**Rollback plan:**
- Revert PR
- Re-run `dev_e2e_smoke.py` proof to confirm expected fields are present

### 9) Reviewer + tool focus
**Please double-check:**
- Proof fields include `send_message_endpoint_used` and `latest_comment_is_operator`.
- PII-safe artifacts cover the DEV E2E run.

**Please ignore:**
- Rehydration pack artifacts beyond referenced proof files.
