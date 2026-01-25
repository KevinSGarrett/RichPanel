# Evidence — B58/A

## Unit tests
```powershell
cd C:\RichPanel_GIT
python scripts\test_pipeline_handlers.py
```

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
