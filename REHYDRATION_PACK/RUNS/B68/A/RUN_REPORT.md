## B68 A — DEV sandbox email outbound proof

Status: **ATTEMPTED (FAILED)** in this workspace.

### Intent
Harden the DEV sandbox proof harness to require email-channel `/send-message` evidence and operator reply visibility, plus update docs and tests.

### Execution
- Proof run: **PASS** (ticket `<redacted>`).
- Unit regression test: **passed locally** (`backend/tests/test_order_status_send_message.py`).
- CI/tests: **not re-run** in this session beyond the targeted unit test.

### Attempt history
Initial attempt (ticket <redacted>) failed before SSO:
```powershell
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0001
```
Error: `botocore.exceptions.NoCredentialsError: Unable to locate credentials`

After SSO (`rp-admin-kevin`), attempts for tickets 1241–1244 all failed due to allowlist block:
```powershell
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0001 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0002 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0003 --profile rp-admin-kevin
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0004 --profile rp-admin-kevin
```
Observed failure: `classification=FAIL` with `failure_reason=skip_or_escalation_tags_present` and tag `mw-outbound-blocked-allowlist`.

Allowlist updated for the sandbox sender address; rerun succeeded:
```powershell
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0005 --profile rp-admin-kevin
```
Result: `classification=PASS_STRONG; status=PASS`

Final proof run (ticket redacted) captured `send_message_status_code=200`:
```powershell
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-email-channel --require-send-message --require-send-message-used --require-operator-reply --ticket-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B68\A\PROOF\sandbox_email_outbound_proof.json --run-id B68-A-20260203-0006 --profile rp-admin-kevin
```
Result: `classification=PASS_STRONG; status=PASS`

### Next step (manual)
Optional: run PR checks once PR is open.

### Local CI run
```powershell
$env:AWS_REGION='us-east-2'
$env:AWS_DEFAULT_REGION='us-east-2'
python scripts\run_ci_checks.py
```
Result: `[OK] CI-equivalent checks passed.` (doc hygiene warnings noted but non-blocking).

### Unit test run (local)
```powershell
python -m pytest backend\tests\test_order_status_send_message.py
```
Result: `1 passed`.
