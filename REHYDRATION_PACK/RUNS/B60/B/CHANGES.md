# B60/B Changes

## Code
- Added outbound allowlist parsing/matching and prod bot-author gating in `backend/src/richpanel_middleware/automation/pipeline.py`, including new skip tags and PII-safe log fields.
- Hardened `scripts/create_sandbox_email_ticket.py` and the `--create-ticket` path in `scripts/dev_e2e_smoke.py` with prod-write acknowledgements and a `--require-allowlist-blocked` proof mode.
- Added unit coverage for allowlist matching, prod author gating, and prod ticket guards in `scripts/test_pipeline_handlers.py` and `scripts/test_e2e_smoke_encoding.py`.
- Documented new outbound allowlist env vars and prod author requirement in `docs/`.

## Artifacts
- Allowlisted ticket proof: `REHYDRATION_PACK/RUNS/B60/B/PROOF/order_status_allowlist_send_proof.json`
- Allowlist-blocked proof: `REHYDRATION_PACK/RUNS/B60/B/PROOF/order_status_allowlist_blocked_proof.json`
- Created-ticket artifacts: `REHYDRATION_PACK/RUNS/B60/B/PROOF/created_ticket_allowlist.json`, `REHYDRATION_PACK/RUNS/B60/B/PROOF/created_ticket_blocked.json`
