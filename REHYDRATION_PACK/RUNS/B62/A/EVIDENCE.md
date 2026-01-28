# Evidence — B62/A

## Scope and safety
- Sandbox/dev only; no production writes.
- All values PII-safe; use `<redacted>` for any real emails or ticket refs.

## Command — lint/unit tests
```powershell
cd C:\RichPanel_GIT
python scripts\run_ci_checks.py
```

## Command — allowlist update (dev, redacted)
```powershell
cd C:\RichPanel_GIT
$scriptPath = Join-Path $env:TEMP "allowlist_update.py"
@'
import boto3
region = "us-east-2"
profile = "rp-admin-kevin"
function_name = "rp-mw-dev-worker"
allowlist_email = "<redacted>"
session = boto3.session.Session(profile_name=profile, region_name=region)
client = session.client("lambda")
config = client.get_function_configuration(FunctionName=function_name)
variables = dict(config.get("Environment", {}).get("Variables", {}) or {})
key = "MW_OUTBOUND_ALLOWLIST_EMAILS"
raw = variables.get(key, "") or ""
entries = [e.strip() for e in raw.split(",") if e.strip()]
if allowlist_email not in entries:
    entries.append(allowlist_email)
variables[key] = ",".join(entries)
client.update_function_configuration(FunctionName=function_name, Environment={"Variables": variables})
client.get_waiter("function_updated").wait(FunctionName=function_name)
print("ALLOWLIST_UPDATED")
'@ | Set-Content -Path $scriptPath
python $scriptPath
Remove-Item -Path $scriptPath -Force
```

## Command — allowlist config check (dev)
```powershell
cd C:\RichPanel_GIT
python scripts\lint_middleware_lambda_config.py --env dev --region us-east-2 --profile rp-admin-kevin
```

## Command (one-command harness)
```powershell
cd C:\RichPanel_GIT
python scripts\sandbox_golden_path_proof.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --run-id b62-20260127-1715Z --allowlist-email <redacted> --proof-path REHYDRATION_PACK\RUNS\B62\A\PROOF\sandbox_golden_path_proof.json
```

## Internal command — create ticket
### Attempt 1
```powershell
cd C:\RichPanel_GIT
C:\Users\kevin\AppData\Local\Programs\Python\Python312\python.exe C:\RichPanel_GIT\scripts\create_sandbox_email_ticket.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --proof-path C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\B62\A\PROOF\created_ticket.json --emit-ticket-ref --profile rp-admin-kevin --from-email <redacted>
```

## Internal command — smoke proof
### Attempt 1
```powershell
cd C:\RichPanel_GIT
C:\Users\kevin\AppData\Local\Programs\Python\Python312\python.exe C:\RichPanel_GIT\scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-openai-routing --require-openai-rewrite --require-outbound --require-send-message --require-operator-reply --followup --proof-path REHYDRATION_PACK\RUNS\B62\A\PROOF\sandbox_golden_path_proof.json --profile rp-admin-kevin --run-id b62-20260127-1715Z --ticket-number <redacted>
```

## Proof excerpt (PII-safe)
```json
{
  "openai_routing_used": true,
  "openai_rewrite_used": true,
  "outbound_send_message_status": 200,
  "send_message_path_confirmed": true,
  "send_message_tag_present": true,
  "latest_comment_is_operator": true,
  "closed_after": true,
  "followup_reply_sent": false,
  "followup_routed_support": true
}
```

## Claude gate audit (CI artifact)
- `REHYDRATION_PACK/RUNS/B62/A/claude_gate_audit.json`
