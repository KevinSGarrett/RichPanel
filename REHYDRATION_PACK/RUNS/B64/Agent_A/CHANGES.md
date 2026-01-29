# Changes — B64/Agent_A

## Code
- Prefer ticket snapshot channel over payload channel when selecting reply path.
- Support `RICHPANEL_BOT_AGENT_ID` with fallback to `RICHPANEL_BOT_AUTHOR_ID`.
- Persist sanitized outbound reply evidence to DDB records for proofing.
- Extend `dev_e2e_smoke.py` with send-message used/status proof fields and CLI flag.

## Tests
- Added/updated outbound email tests for channel preference, bot env var, and send-message failures.
- Updated smoke proof encoding tests for new proof fields and criteria.
- Added worker evidence persistence tests for outbound results.

## Docs/Config
- Documented bot agent env var and channel precedence in reply-path docs.
- Updated secrets registry + lint output for bot agent/author id.
- Wired `RICHPANEL_BOT_AGENT_ID` into CDK worker environment.

## Artifacts
- `REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/order_status_outbound_operator_reply_proof.json`
- `REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/created_ticket_order_status.json`
- `REHYDRATION_PACK/RUNS/B64/Agent_A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B64/Agent_A/RUN_REPORT.md`
