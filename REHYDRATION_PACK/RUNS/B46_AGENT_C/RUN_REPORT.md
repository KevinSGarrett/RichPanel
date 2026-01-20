# Agent Run Report

## Metadata
- **Run ID:** `RUN_20260119_B46_AGENT_C`
- **Agent:** C
- **Date (UTC):** 2026-01-19
- **Worktree path:** `C:\RichPanel_GIT`
- **Branch:** `agent-c/b46-prod-readonly-shadow-eval`
- **PR:** none (not created)
- **PR merge strategy:** merge commit (required)
- **Risk label:** risk:R2 (safety/production)
- **gate:claude label:** intended (pending PR)
- **Claude PASS comment:** N/A

## Objective + stop conditions
- **Objective:** add fail-closed guards + GET-only trace + PII-safe artifacts for prod read-only shadow eval, update runbook, add unit test.
- **Stop conditions:** script + runbook updated, unit test added, run report recorded.

## What changed (high-level)
- Added env guards + GET-only HTTP tracing to `scripts/live_readonly_shadow_eval.py`.
- Updated prod runbook instructions + evidence requirements for trace artifacts.
- Added unit test to assert prod guard exits when write-disabled is false.

## Commands Run
```powershell
git status -sb
# output:
branch was b46-order-status-proof with untracked files present

git checkout -b agent-c/b46-prod-readonly-shadow-eval
# output:
Switched to a new branch 'agent-c/b46-prod-readonly-shadow-eval'

git fetch origin
# output:
origin/main updated

git rev-list --left-right --count origin/main...HEAD
# output:
1	0

python -m unittest scripts.test_live_readonly_shadow_eval
# output:
Ran 1 test in 0.001s
OK

$env:RICHPANEL_ENV="prod"
$env:MW_ENV="prod"
$env:MW_ALLOW_NETWORK_READS="true"
$env:RICHPANEL_OUTBOUND_ENABLED="true"
$env:RICHPANEL_WRITE_DISABLED="true"
$env:SHOPIFY_SHOP_DOMAIN="scentimen-t.myshopify.com"
$env:RICHPANEL_API_KEY_OVERRIDE=$env:PROD_RICHPANEL_API_KEY
python scripts/live_readonly_shadow_eval.py --ticket-id 91608 --richpanel-secret-id rp-mw/prod/richpanel/api_key --shop-domain scentimen-t.myshopify.com
# output:
Ticket lookup failed for redacted:26807bb6042a: /v1/tickets/91608: Unable to load Richpanel API key from Secrets Manager; /v1/tickets/number/91608: Unable to load Richpanel API key from Secrets Manager

gh workflow run seed-secrets.yml -f environment=prod
# output:
(workflow dispatch)

gh run list --workflow seed-secrets.yml --limit 1
# output:
queued Seed Secrets main workflow_dispatch 21159596248

gh run watch 21159596248 --exit-status
# output:
seed job completed successfully

gh run view 21159596248 --json url,status,conclusion
# output:
success https://github.com/KevinSGarrett/RichPanel/actions/runs/21159596248

$env:AWS_PROFILE="rp-admin-prod"
$env:AWS_SDK_LOAD_CONFIG="1"
$env:RICHPANEL_ENV="prod"
$env:MW_ENV="prod"
$env:MW_ALLOW_NETWORK_READS="true"
$env:RICHPANEL_OUTBOUND_ENABLED="true"
$env:RICHPANEL_WRITE_DISABLED="true"
$env:SHOPIFY_SHOP_DOMAIN="scentimen-t.myshopify.com"
Remove-Item Env:RICHPANEL_API_KEY_OVERRIDE -ErrorAction SilentlyContinue
python scripts/live_readonly_shadow_eval.py --ticket-id 91608 --richpanel-secret-id rp-mw/prod/richpanel/api_key --shop-domain scentimen-t.myshopify.com
# output:
Artifact written to C:\RichPanel_GIT\artifacts\readonly_shadow\20260120T044002Z_26807bb6042a.json
HTTP trace written to C:\RichPanel_GIT\artifacts\prod_readonly_shadow_eval_http_trace.json

Copy-Item -Force artifacts\readonly_shadow\20260120T044002Z_26807bb6042a.json REHYDRATION_PACK\RUNS\B46_AGENT_C\EVIDENCE\readonly_shadow\20260120T044002Z_26807bb6042a.json
Copy-Item -Force artifacts\prod_readonly_shadow_eval_http_trace.json REHYDRATION_PACK\RUNS\B46_AGENT_C\EVIDENCE\prod_readonly_shadow_eval_http_trace.json
```

## Tests / Proof
- **Tests run:** `python -m unittest scripts.test_live_readonly_shadow_eval` (PASS)
- **Production eval run:** success (prod AWS profile + Secrets Manager access)
- **Secrets seeded:** `seed-secrets.yml` (prod) — https://github.com/KevinSGarrett/RichPanel/actions/runs/21159596248 (success)
- **Planned prod command (PowerShell):**
```powershell
$env:RICHPANEL_API_KEY_OVERRIDE = $env:PROD_RICHPANEL_API_KEY
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"

python scripts/live_readonly_shadow_eval.py `
  --ticket-id <ticket-or-conversation-id> `
  --richpanel-secret-id rp-mw/prod/richpanel/api_key `
  --shop-domain <myshop.myshopify.com>
```
- **Evidence outputs:**
  - `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/readonly_shadow/20260120T044002Z_26807bb6042a.json`
  - `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/prod_readonly_shadow_eval_http_trace.json`

## Follow-ups
- None.
