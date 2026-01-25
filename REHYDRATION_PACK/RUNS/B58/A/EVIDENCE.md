# Evidence — B58/A

## Unit tests
```powershell
cd C:\RichPanel_GIT
python scripts\test_pipeline_handlers.py
python scripts\test_llm_routing.py
python scripts\test_e2e_smoke_encoding.py
```

## CI-equivalent checks
```powershell
cd C:\RichPanel_GIT
python scripts\run_ci_checks.py --ci | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B58\A\CI_RUN_OUTPUT.txt
```

Output:
```
[OK] REHYDRATION_PACK validated (mode=build).
[OK] GPT-5.x defaults enforced (no GPT-4 family strings found).
[OK] No unapproved protected deletes/renames detected (git diff HEAD~1...HEAD).
[OK] CI-equivalent checks passed.
```

Full log:
- `REHYDRATION_PACK/RUNS/B58/A/CI_RUN_OUTPUT.txt`

## Email outbound path snippet
Command:
```powershell
cd C:\RichPanel_GIT
python -c "import os, sys; sys.path.insert(0, r'C:\RichPanel_GIT'); from scripts.test_pipeline_handlers import _RecordingExecutor; from richpanel_middleware.automation.pipeline import execute_order_status_reply, plan_actions; from richpanel_middleware.ingest.envelope import build_event_envelope; os.environ['RICHPANEL_BOT_AUTHOR_ID']='agent-123'; envelope=build_event_envelope({'ticket_id':'t-email','order_id':'ord-1','shipping_method':'2 business days','created_at':'2024-12-20T00:00:00Z','message':'Where is my order?'}); plan=plan_actions(envelope, safe_mode=False, automation_enabled=True); executor=_RecordingExecutor(ticket_channel='email'); execute_order_status_reply(envelope, plan, safe_mode=False, automation_enabled=True, allow_network=True, outbound_enabled=True, richpanel_executor=executor); print('paths:', [call['path'] for call in executor.calls]);"
```

Output:
```
paths: ['/v1/tickets/t-email', '/v1/tickets/t-email/send-message', '/v1/tickets/t-email', '/v1/tickets/t-email', '/v1/tickets/t-email/add-tags']
```

## Sandbox proof (PASS)
Notes:
- Dev stack deployed via `deploy-dev.yml` workflow.
- `RICHPANEL_BOT_AUTHOR_ID` set on `rp-mw-dev-worker` to dedicated bot (id_hash=`847bae85`).

Command (PII-safe, redacted ticket number):
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --scenario order_status --ticket-number <redacted> --no-require-outbound --require-openai-routing --require-openai-rewrite --require-send-message --require-operator-reply --followup --run-id B58-SANDBOX-20260125150840 --proof-path REHYDRATION_PACK\RUNS\B58\A\PROOF\order_status_email_sandbox_proof.json
```

Output:
```
[RESULT] classification=PASS_STRONG; status=PASS; failure_reason=none
```

Proof artifact:
- `REHYDRATION_PACK/RUNS/B58/A/PROOF/order_status_email_sandbox_proof.json`
