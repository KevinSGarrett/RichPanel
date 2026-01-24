# B54 Changes

## Code
- Added outbound proof gating + required CLI aliases (`--require-outbound`, `--followup`, `--json`) and proof fields in `scripts/dev_e2e_smoke.py`.
- Added comment-count fallback to infer outbound message evidence when message_count fields are missing in Richpanel ticket payloads.
- Added dev-only OpenAI routing primary override (payload-gated) in `llm_routing.py` and `pipeline.py`.
- Added PII-safe `scripts/find_recent_sandbox_ticket.py` helper for listing recent sandbox tickets.
- Added outbound evidence + ticket snapshot fallback unit tests in `scripts/test_e2e_smoke_encoding.py`.

## Artifacts
- Proof JSON (PASS_STRONG): `REHYDRATION_PACK/RUNS/B54/B/PROOF/order_status_outbound_followup_proof.json`
- Earlier failed attempts kept for traceability in `REHYDRATION_PACK/RUNS/B54/B/PROOF/`.
