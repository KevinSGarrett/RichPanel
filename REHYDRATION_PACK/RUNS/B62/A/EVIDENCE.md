# Evidence — B62/A

## Scope and safety
- Sandbox/dev only; no production writes.
- All values PII-safe; use `<redacted>` for any real emails or ticket refs.

## Command — lint/unit tests
```powershell
cd C:\RichPanel_GIT
python scripts\run_ci_checks.py
```

## Command — patch coverage summary (local)
```powershell
cd C:\RichPanel_GIT
coverage run -m unittest discover -s scripts -p "test_*.py"
coverage json -o coverage_local.json
$scriptPath = Join-Path $env:TEMP "patch_coverage_summary.py"
@'
import json
import subprocess
from pathlib import Path

root = Path(r"C:\RichPanel_GIT")
coverage = json.loads((root / "coverage_local.json").read_text(encoding="utf-8"))
files = coverage.get("files", {})

result = subprocess.run(
    [
        "git",
        "diff",
        "origin/main...HEAD",
        "--unified=0",
        "--",
        "scripts/dev_e2e_smoke.py",
        "scripts/create_sandbox_email_ticket.py",
        "scripts/b62_sandbox_golden_path.py",
        "scripts/sandbox_golden_path_proof.py",
        "scripts/test_e2e_smoke_encoding.py",
        "scripts/test_b62_golden_path.py",
        "scripts/test_create_sandbox_email_ticket.py",
    ],
    cwd=str(root),
    text=True,
    capture_output=True,
)

diffs = result.stdout.splitlines()
changed = {}
current_file = None
for line in diffs:
    if line.startswith("+++ b/"):
        current_file = line[len("+++ b/"):].strip().replace("/", "\\")
        continue
    if line.startswith("@@") and current_file:
        parts = line.split()
        for part in parts:
            if part.startswith("+") and "," in part:
                start, count = part[1:].split(",")
                start = int(start)
                count = int(count)
                lines = set(range(start, start + count)) if count else set()
                changed.setdefault(current_file, set()).update(lines)
            elif part.startswith("+") and part[1:].isdigit():
                start = int(part[1:])
                changed.setdefault(current_file, set()).add(start)

lines_out = ["Patch coverage (executable lines):"]
for file_path, lines in sorted(changed.items()):
    data = files.get(file_path)
    if not data:
        lines_out.append(f"{file_path}: no coverage data")
        continue
    executed = set(data.get("executed_lines", []))
    missing = set(data.get("missing_lines", []))
    relevant = executed | missing
    relevant_changed = lines & relevant
    total = len(relevant_changed)
    covered = len(relevant_changed & executed)
    percent = 100.0 * covered / total if total else 100.0
    lines_out.append(f"{file_path}: {covered}/{total} covered ({percent:.1f}%)")

summary_path = root / "REHYDRATION_PACK" / "RUNS" / "B62" / "A" / "PROOF" / "patch_coverage_summary.txt"
summary_path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
print(f"[OK] Wrote patch coverage summary to {summary_path}")
'@ | Set-Content -Path $scriptPath
python $scriptPath
Remove-Item -Path $scriptPath -Force
```

## Patch coverage summary (PII-safe)
```text
Patch coverage (executable lines):
scripts\b62_sandbox_golden_path.py: 225/225 covered (100.0%)
scripts\create_sandbox_email_ticket.py: 4/4 covered (100.0%)
scripts\dev_e2e_smoke.py: 75/75 covered (100.0%)
scripts\sandbox_golden_path_proof.py: 4/4 covered (100.0%)
scripts\test_b62_golden_path.py: 237/237 covered (100.0%)
scripts\test_create_sandbox_email_ticket.py: 38/38 covered (100.0%)
scripts\test_e2e_smoke_encoding.py: 104/104 covered (100.0%)
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
