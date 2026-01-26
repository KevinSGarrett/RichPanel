# B59 Changes

## Code
- Added `scripts/create_sandbox_email_ticket.py` to create sandbox email tickets via the Richpanel API with PII-safe output.
- Added auto-ticket flags and creation flow to `scripts/dev_e2e_smoke.py`, plus redaction for new inputs.
- Extended `scripts/test_e2e_smoke_encoding.py` to cover redaction of auto-ticket flags.
- Expanded auto-ticket payloads with email `to` address and customer profile defaults to match Richpanel API expectations.

## Artifacts
- Created-ticket template: `REHYDRATION_PACK/RUNS/B59/B/PROOF/created_ticket.json`
- Auto-ticket proof template: `REHYDRATION_PACK/RUNS/B59/B/PROOF/order_status_operator_reply_followup_proof_autoticket.json`
