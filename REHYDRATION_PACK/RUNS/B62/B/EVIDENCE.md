# Evidence - B62/B

## Scope and safety

- Dev-only run; no production writes.
- All identifiers redacted; no raw emails, order numbers, or ticket IDs.

## Unit tests

```powershell
cd C:\RichPanel_GIT
python scripts\test_pipeline_handlers.py 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B62\B\PROOF\unit_test_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B62/B/PROOF/unit_test_output.txt`

## CI-equivalent (local)

```powershell
cd C:\RichPanel_GIT
python scripts\run_ci_checks.py --ci 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B62\B\PROOF\run_ci_checks_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B62/B/PROOF/run_ci_checks_output.txt`
- Result: failed due to regenerated docs/registry changes already present in repo; see log tail.

## dev_e2e_smoke (email send-message path)

```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-outbound --require-send-message-path --require-operator-reply --create-ticket --create-ticket-proof-path REHYDRATION_PACK\RUNS\B62\B\PROOF\created_ticket.json --proof-path REHYDRATION_PACK\RUNS\B62\B\PROOF\dev_e2e_smoke_proof.json --profile rp-admin-kevin --run-id b62-20260128-b
```

- Output: `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_output.txt`
- Created ticket proof: `REHYDRATION_PACK/RUNS/B62/B/PROOF/created_ticket.json`
- Proof JSON: `REHYDRATION_PACK/RUNS/B62/B/PROOF/dev_e2e_smoke_proof.json`

Proof excerpt (PII-safe):

```json
{
  "ticket_channel": "email",
  "send_message_path_confirmed": true,
  "latest_comment_is_operator": true,
  "closed_after": true
}
```

## Claude gate (real)

- Run: https://github.com/KevinSGarrett/RichPanel/actions/runs/21439788645
- Audit artifact: `REHYDRATION_PACK/RUNS/B62/B/PROOF/claude_gate_audit.json`

## Non-email outbound proof

- Unit test coverage:
  - `test_outbound_non_email_uses_comment_path`
  - `test_outbound_allowlist_blocks_non_email_channel`
- Attempted non-email ticket creation (Richpanel API rejects non-email channel values):

```powershell
cd C:\RichPanel_GIT
python scripts\create_sandbox_chat_ticket.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --proof-path REHYDRATION_PACK\RUNS\B62\B\PROOF\created_chat_ticket.json --emit-ticket-ref --profile rp-admin-kevin --channel chat 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B62\B\PROOF\create_chat_ticket_error.txt
```

- Output: `REHYDRATION_PACK/RUNS/B62/B/PROOF/create_chat_ticket_error.txt`
- Note: the `created_chat_ticket.json` artifact is not produced because the API returns 400.
- Limitation: Richpanel ticket creation API returns `Invalid value` for non-email `ticket.via.channel`; validated via deterministic unit tests instead.
