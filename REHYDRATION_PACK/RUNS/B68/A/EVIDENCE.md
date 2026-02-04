## Evidence — B68 A

### Proof run (PASS)
Initial attempt failed due to missing AWS credentials; subsequent attempts were blocked by allowlist until the allowlist update. Final run passed.

Attempted commands (ticket numbers redacted):
```powershell
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0001
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0002 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0003 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0004 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0005 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0006 --profile rp-admin-kevin
```

### Notes
- Shopify is live read-only; no test orders created.
- Proof JSON is PII-safe and contains no real ticket content.
- Failures:
  - `botocore.exceptions.NoCredentialsError: Unable to locate credentials`
  - `classification=FAIL` with `failure_reason=skip_or_escalation_tags_present` and tag `mw-outbound-blocked-allowlist`
- Success:
  - `classification=PASS_STRONG; status=PASS` after allowlist update

### Proof excerpt (latest run)
From `REHYDRATION_PACK/RUNS/B68/A/PROOF/sandbox_email_outbound_proof.json`:
```json
{
  "proof_fields": {
    "ticket_channel": "email",
    "outbound_endpoint_used": "/send-message",
    "send_message_status_code": 200,
    "latest_comment_is_operator": true,
    "latest_comment_source": null,
    "outbound_failure_classification": null
  },
  "result": {
    "status": "PASS"
  }
}
```

### Local CI run
```powershell
$env:AWS_REGION='us-east-2'
$env:AWS_DEFAULT_REGION='us-east-2'
python scripts\run_ci_checks.py
```
Result: `[OK] CI-equivalent checks passed.` (doc hygiene warnings are non-blocking).

### Unit regression test (local)
```powershell
python -m pytest backend\tests\test_order_status_send_message.py
```
Result: `1 passed`.

### Doc grep (Shopify sandbox/dev store)
```powershell
rg -n "Shopify sandbox|dev shopify store|shopify dev store" docs
```
Result: only explicit “no Shopify sandbox/dev store” guidance remains (see paths listed in command output).