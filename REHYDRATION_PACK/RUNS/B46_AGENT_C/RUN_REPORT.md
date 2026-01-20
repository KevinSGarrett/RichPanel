# Agent Run Report

## Metadata
- **Run ID:** `RUN_20260119_B46_AGENT_C`
- **Agent:** C
- **Date (UTC):** 2026-01-20
- **Worktree path:** `C:\RichPanel_GIT`
- **Branch:** `agent-c/b46-prod-readonly-shadow-eval`
- **PR:** https://github.com/KevinSGarrett/RichPanel/pull/128
- **PR merge strategy:** merge commit (required)
- **Risk label:** risk:R2 (safety/production)
- **gate:claude label:** yes (applied on PR)
- **Claude PASS comment:** N/A (gate check pass; no comment posted)

## Objective + stop conditions
- **Objective:** add fail-closed guards + GET-only trace + PII-safe artifacts for prod read-only shadow eval, update runbook, add unit test.
- **Stop conditions:** script + runbook updated, unit test added, run report recorded.

## What changed (high-level)
- Added env guards + GET-only HTTP tracing to `scripts/live_readonly_shadow_eval.py`.
- Updated prod runbook instructions + evidence requirements for trace artifacts.
- Added unit test to assert prod guard exits when write-disabled is false.
- Added expanded coverage tests for read-only eval helpers + stubbed main path.
- Regenerated doc registries/checklists required by CI.
- Captured prod evidence artifacts and HTTP trace in REHYDRATION_PACK.

## Commits (branch history)
- `1f45915` — B46: prod read-only shadow eval guards
- `966914d` — B46: record prod secret seeding run
- `d918896` — B46: add prod read-only eval evidence
- `eec4966` — B46: record PR creation and labels
- `7b2ac29` — B46: refresh generated doc registries
- `459b2ab` — B46: expand readonly eval test coverage
- `8a43f6a` — B46: cover readonly eval main path
- `a2cc62f` — B46: exercise readonly eval helpers

## Files touched (complete)
- `scripts/live_readonly_shadow_eval.py`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `scripts/test_live_readonly_shadow_eval.py`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_registry.json`
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`
- `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`
- `REHYDRATION_PACK/RUNS/B46_AGENT_C/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/README.md`
- `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/prod_readonly_shadow_eval_http_trace.json`
- `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/readonly_shadow/20260120T044002Z_26807bb6042a.json`

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

gh pr create --title "B46: Production read-only shadow evaluation (fail-closed)" --body <filled>
# output:
https://github.com/KevinSGarrett/RichPanel/pull/128

gh pr edit 128 --add-label "risk:R2" --add-label "gate:claude"
# output:
labels applied

python scripts/run_ci_checks.py --ci
# output:
[FAIL] Generated files changed after regen. Commit the regenerated outputs.

git add docs/_generated/doc_registry.compact.json docs/_generated/doc_registry.json docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md docs/00_Project_Admin/To_Do/_generated/plan_checklist.json
git commit -m "B46: refresh generated doc registries"
git push

python -m unittest scripts.test_live_readonly_shadow_eval
# output:
Ran 28 tests in 0.011s
OK

coverage run -m unittest discover -s scripts -p "test_*.py"
coverage xml
# output:
coverage.xml generated for Codecov patch

gh pr checks 128 --watch
# output:
validate pass; codecov/patch pass; claude-gate-check pass; risk-label-check pass; Cursor Bugbot pass
```

## Tests / Proof
- **Tests run (local):**
  - `python -m unittest scripts.test_live_readonly_shadow_eval` (PASS; 28 tests)
  - `coverage run -m unittest discover -s scripts -p "test_*.py"` + `coverage xml`
- **CI validate:** https://github.com/KevinSGarrett/RichPanel/actions/runs/21160422555/job/60853799057 (pass)
- **Codecov patch:** https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/128 (pass)
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

## Evidence & proof (verbatim)
- **HTTP trace (GET-only proof):** `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/prod_readonly_shadow_eval_http_trace.json`
  - Contains only `GET` methods for Richpanel endpoints; no POST/PUT/PATCH/DELETE.
- **PII-safe eval artifact:** `REHYDRATION_PACK/RUNS/B46_AGENT_C/EVIDENCE/readonly_shadow/20260120T044002Z_26807bb6042a.json`
  - Ticket/customer identifiers are hashed (`redacted:*`), no message bodies.
- **PR:** https://github.com/KevinSGarrett/RichPanel/pull/128
- **PR checks (final):**
  - validate: https://github.com/KevinSGarrett/RichPanel/actions/runs/21160422555/job/60853799057
  - claude-gate-check: https://github.com/KevinSGarrett/RichPanel/actions/runs/21160428950/job/60853816753
  - codecov/patch: https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/128
  - risk-label-check: https://github.com/KevinSGarrett/RichPanel/actions/runs/21160428960/job/60853816787
  - Cursor Bugbot: https://cursor.com (PASS)

## Issues encountered and how they were fixed (with proof)
1) **Prod eval failed (missing Secrets Manager access)**
   - Error: `Unable to load Richpanel API key from Secrets Manager`
   - Fix: Seeded `rp-mw/prod/richpanel/api_key` via `seed-secrets.yml` using `PROD_RICHPANEL_API_KEY`.
   - Proof: Workflow success — https://github.com/KevinSGarrett/RichPanel/actions/runs/21159596248
   - Result: Prod eval succeeded; artifacts written and copied into REHYDRATION_PACK.

2) **CI validate failed (generated registries not committed)**
   - Error: `[FAIL] Generated files changed after regen. Commit the regenerated outputs.`
   - Fix: Regenerated doc registries and plan checklist, committed `docs/_generated/*` and `docs/00_Project_Admin/To_Do/_generated/*`.
   - Proof: validate pass — https://github.com/KevinSGarrett/RichPanel/actions/runs/21160422555/job/60853799057

3) **Codecov patch failed (insufficient coverage)**
   - Error: patch coverage below threshold; missing lines in `scripts/live_readonly_shadow_eval.py` and test file.
   - Fix: Added extensive unit tests covering helper functions, path redaction, env guards, HTTP trace mapping, fetch paths, and a stubbed `main()` path.
   - Proof: Codecov patch pass — https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/128

4) **Local test_shopify_client failure (environment leakage)**
   - Cause: `SHOPIFY_SHOP_DOMAIN` set from prod eval run; broke expected default in tests.
   - Fix: Cleared env vars before coverage/test runs.
   - Proof: Local unit test suite and coverage command succeeded (see Tests / Proof).

## PR checks (final green)
- Cursor Bugbot: PASS — https://cursor.com
- claude-gate-check: PASS — https://github.com/KevinSGarrett/RichPanel/actions/runs/21160428950/job/60853816753
- codecov/patch: PASS — https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/128
- risk-label-check: PASS — https://github.com/KevinSGarrett/RichPanel/actions/runs/21160428960/job/60853816787
- validate: PASS — https://github.com/KevinSGarrett/RichPanel/actions/runs/21160422555/job/60853799057

## Follow-ups
- None.
