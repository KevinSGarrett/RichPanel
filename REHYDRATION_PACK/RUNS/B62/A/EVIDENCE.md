# Evidence — B62/A

## Scope and safety

- Sandbox/dev only; no production writes.
- All values PII-safe; use `<redacted>` for any real emails or ticket refs.

## Command (one-command harness)

```powershell
cd C:\RichPanel_GIT
C:\Users\kevin\AppData\Local\Programs\Python\Python312\python.exe C:\RichPanel_GIT\scripts\b62_sandbox_golden_path.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --run-id b62-20260128-0545Z --allowlist-email <redacted> --order-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B62\A\PROOF\sandbox_golden_path_proof.json
```

## Internal command — create ticket

### Attempt 1 (create ticket)

```powershell
cd C:\RichPanel_GIT
C:\Users\kevin\AppData\Local\Programs\Python\Python312\python.exe C:\RichPanel_GIT\scripts\create_sandbox_email_ticket.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --proof-path C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\B62\A\PROOF\created_ticket.json --emit-ticket-ref --profile rp-admin-kevin --from-email <redacted>
```

## Internal command — smoke proof

### Attempt 1 (smoke proof)

```powershell
cd C:\RichPanel_GIT
C:\Users\kevin\AppData\Local\Programs\Python\Python312\python.exe C:\RichPanel_GIT\scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-openai-routing --require-openai-rewrite --require-order-match-by-number --require-outbound --require-send-message --require-operator-reply --followup --proof-path REHYDRATION_PACK\RUNS\B62\A\PROOF\sandbox_golden_path_proof.json --profile rp-admin-kevin --run-id b62-20260128-0545Z --order-number <redacted> --ticket-number <redacted>
```

## Proof excerpt (PII-safe)

```json
{
  "openai_routing_used": true,
  "openai_rewrite_used": true,
  "order_match_by_number": true,
  "outbound_send_message_status": 200,
  "send_message_path_confirmed": true,
  "send_message_tag_present": true,
  "latest_comment_is_operator": true,
  "closed_after": true,
  "followup_reply_sent": false,
  "followup_routed_support": true
}
```

## CI / unit tests

```powershell
cd C:\RichPanel_GIT
python scripts/run_ci_checks.py
```

- Output: `REHYDRATION_PACK\RUNS\B62\A\PROOF\run_ci_checks_output.txt`

## Claude gate audit (R2)

- `REHYDRATION_PACK\RUNS\B62\A\claude_gate_audit.json`

## Patch coverage summary

- `REHYDRATION_PACK\RUNS\B62\A\PROOF\patch_coverage_summary.txt`
