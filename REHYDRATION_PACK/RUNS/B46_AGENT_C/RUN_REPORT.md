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
```

## Tests / Proof
- **Tests run:** `python -m unittest scripts.test_live_readonly_shadow_eval` (PASS)
- **Production eval run:** failed (missing Secrets Manager access or prod key override)
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
- **Expected evidence outputs (after prod run):**
  - `artifacts/readonly_shadow/<timestamp>_<ticket_hash>.json`
  - `artifacts/prod_readonly_shadow_eval_http_trace.json`

## Follow-ups
- Run `python -m unittest scripts.test_live_readonly_shadow_eval` locally.
- Execute prod eval command and attach artifacts to `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/`.
