# CI and GitHub Actions Runbook (for Cursor Agents)

Last updated: 2026-01-05  
Status: Canonical

This runbook defines how agents must keep CI green and how to self-fix when GitHub Actions fails.

---

## 1) CI contract
A change is not considered “done” until:

- local CI-equivalent checks pass (`python scripts/run_ci_checks.py`)
- GitHub Actions checks are green (unless explicitly waived by PM)

### What runs in CI (ci.yml)
Every PR automatically runs:

1. `npm install` / `npm ci` for `infra/cdk`
2. `npm run build` for the CDK package
3. `npx cdk synth` to confirm the stack renders cleanly
4. `python scripts/run_ci_checks.py --ci` for repo-wide policy + hygiene validation

No steps are optional; your change must keep this pipeline green.

---

## 2) Local CI-equivalent checks
Run:
```bash
python scripts/run_ci_checks.py
```

### Windows note: PowerShell 5.x does **not** support `&&`
If you copy/paste examples that use `&&` (common in bash/zsh), they will fail in **Windows PowerShell 5.x**.

Use **separate lines** or `;` instead:
```powershell
# ✅ PowerShell-safe: separate lines
python scripts/run_ci_checks.py
git status

# ✅ PowerShell-safe: same line with ;
python scripts/run_ci_checks.py; git status

# ❌ NOT supported in Windows PowerShell 5.x
python scripts/run_ci_checks.py && git status
```

### PowerShell helper (Windows)
Use the wrapper so you get consistent status output and argument handling:
```powershell
pwsh -File scripts/ci.ps1
```
or from an existing PowerShell session:
```powershell
.\scripts\ci.ps1 -- --ci
```
Everything after `--` is passed through to `python scripts/run_ci_checks.py`.

This runs:
- rehydration pack validation
- docs/reference registry validation
- doc hygiene checks
- plan sync validation
- protected delete checks (when git diff range is available)

If this fails locally, **fix before pushing**.

### Mypy “asset.\* not a valid package name” (CDK outputs)
- Cause: `cdk synth` writes `infra/cdk/cdk.out/asset.<hash>` folders; mypy treats the dotted folder name as a package and errors.
- Fix: use the repo-root `mypy.ini` (limits checks to `backend/src` + `scripts` and excludes generated trees) and delete any local `infra/cdk/cdk.out` leftovers before re-running mypy.

---

## 3) Bugbot PR review (Cursor)
Bugbot is a **standard part of our hardened PR loop**, but it is **not a hard CI blocker yet**. Treat it as required human process: run it, read it, and address findings (or explicitly document why not) before merging.

### “Extensions are not CLI” (Cursor/VS Code)
Do not assume a VS Code/Cursor extension can be triggered from the terminal.

- **Extensions are UI/editor integrations**: you can’t reliably “run” them via CLI in CI or scripts.
- **Enforcement lives in CI + scripts**: rely on `python scripts/run_ci_checks.py` and GitHub Actions as the source of truth.
- **Bugbot is triggered via GitHub PR comments** (UI or `gh`), not by a local extension command.

### How to trigger a review (mention-only mode)
If Bugbot is configured to only run on mention, trigger it by adding one of these PR comments:
- `bugbot run`
- `@cursor review`

### PowerShell-safe `gh` examples
Post the trigger comment:
```powershell
# Trigger Bugbot on a specific PR number
gh pr comment 123 -b 'bugbot run'
# or
gh pr comment 123 -b '@cursor review'
```

Then view PR comments (including Bugbot output):
```powershell
gh pr view 123 --comments
```

Tip: if you’re already on the PR branch, you can let `gh` infer the PR:
```powershell
$pr = gh pr view --json number --jq '.number'
gh pr comment $pr -b 'bugbot run'
gh pr view $pr --comments
```

### Alternative trigger: workflow dispatch (Actions tab)
If you can’t (or don’t want to) comment from the UI/`gh`, you can trigger Bugbot via an on-demand workflow that **posts the comment for you**:

- Workflow: `.github/workflows/bugbot-review.yml`
- Inputs:
  - `pr_number` (required)
  - `comment_body` (optional; defaults to `@cursor review`)

PowerShell-safe examples:
```powershell
# Posts the default comment body (@cursor review)
gh workflow run bugbot-review.yml -f pr_number=123

# Override the posted comment body if needed
gh workflow run bugbot-review.yml -f pr_number=123 -f comment_body='bugbot run'
```

### Merge policy (auditability)
We require **merge commits only** for auditability and traceability.
- Use **auto-merge** and the merge-commit method:
  - `gh pr merge --auto --merge --delete-branch`
- **Do not squash merge**. Squash merging is intentionally disabled to preserve per-commit history and support evidence/audit workflows.

---

## 4) When GitHub Actions fails (red status)

### Step 1 — Identify the failing job
Preferred (if GitHub CLI is available and authenticated):
```bash
gh run list --limit 5
gh run view <RUN_ID> --log
```

> PowerShell note: avoid embedding `| jq someFilter` inside quoted strings. Use the built-in `--json` + `--jq` flags so the command stays shell-safe, e.g.:
> ```
> gh run list --limit 5 --json databaseId,headBranch,status --jq '.[] | {run_id:.databaseId, branch:.headBranch, status}'
> ```
> This works in PowerShell without needing jq pipes.

Fallback:
- open the Actions page in GitHub UI
- copy/paste the failing log excerpt into the PM cycle notes

### Step 2 — Reproduce locally
- find the failing step name
- run the equivalent script/test locally
- if reproduction is not possible (rare), record why

### Step 3 — Fix the problem
- implement the minimal fix
- rerun local checks
- commit the fix with a clear message:
  - `RUN:<RUN_ID> fix CI: <short reason>`

### Step 4 — Document the failure and fix
1) Add/update issue log:
   - `docs/00_Project_Admin/Issue_Log.md`
2) Create an issue detail file:
   - `docs/00_Project_Admin/Issues/<ISSUE_ID>.md`
   Include:
   - what failed and where (job/step)
   - affected files/sections
   - root cause analysis
   - fix description
   - prevention notes (if any)

### Step 5 — Add test evidence
- `docs/08_Testing_Quality/Test_Evidence_Log.md`
- raw artifacts: `qa/test_evidence/<RUN_ID>/<ARTIFACTS>/`

### Step 6 — Push and verify green
- push the fix
- confirm the workflow is green
- update `REHYDRATION_PACK/GITHUB_STATE.md`

---

## 5) Dev E2E smoke workflow

The “Dev E2E Smoke” workflow (`.github/workflows/dev-e2e-smoke.yml`) continuously validates the dev stack by sending a synthetic webhook and confirming the worker Lambda writes idempotency, conversation state, and audit records to DynamoDB.

### When to run it
- After touching backend Lambda logic, webhook auth, or infra that touches ingress/queue/worker paths.
- Before handing off a PR that affects event flow.

### How to run (PowerShell-safe)
```powershell
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run dev-e2e-smoke.yml --ref <branch-name> -f event-id=$eventId
gh run watch --exit-status
gh run view --json url --jq '.url'
```
Notes:
- `gh workflow run` accepts either the filename or workflow name; we use the file to avoid spaces.
- `-f event-id=<VALUE>` is PowerShell-safe because it avoids nested quotes/pipes.
- `gh run watch` exits non-zero if the workflow fails—treat that as a blocking issue.
- `gh run view --json url --jq '.url'` prints the run URL; capture it in the rehydration pack evidence table.

### Evidence expectations
- Copy the GitHub Actions run URL and the job summary block (ingress URL, queue URL, DynamoDB tables, log group, CloudWatch Logs) into `REHYDRATION_PACK/RUNS/<RUN_ID>/C/TEST_MATRIX.md`.
- Record the explicit confirmations from the summary that idempotency, conversation state, and audit records were written (event_id + conversation_id observed) and link the DynamoDB consoles for each table.
- Capture the CloudWatch dashboard name (`rp-mw-<env>-ops`) and alarm names (`rp-mw-<env>-dlq-depth`, `rp-mw-<env>-worker-errors`, `rp-mw-<env>-worker-throttles`, `rp-mw-<env>-ingress-errors`) from the summary; if the stack is missing any, state “no dashboards/alarms surfaced”.
- Paste the smoke summary lines that confirm routing category/tags and the order_status_draft_reply plan + draft_replies count (safe fields only; no message bodies).
- If the workflow fails, include the failure log excerpt plus the remediation plan in `RUN_SUMMARY.md`.

## 6) Staging E2E smoke workflow

The “Staging E2E Smoke” workflow (`.github/workflows/staging-e2e-smoke.yml`) validates the staging stack end-to-end using the same script as dev, but under the staging deploy role.

### When to run it
- Immediately after `Deploy Staging Stack` reports success (either via workflow dispatch or automation).
- Before handing off any change that touches ingress, queues, Secrets Manager, or worker execution paths targeting staging.

### How to run (PowerShell-safe)
```powershell
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
$null = gh workflow run staging-e2e-smoke.yml --ref main -f event-id=$eventId
$runId = gh run list --workflow staging-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $runId --exit-status
$runUrl = gh run view $runId --json url --jq '.url'
$runUrl
```
Guidance:
- Run against `--ref main` to prove the deployed artifact is healthy.
- `gh run list` scoped to `staging-e2e-smoke.yml` + `--branch main` surfaces the run ID you just dispatched; reuse it for `gh run watch` and `gh run view`.
- `gh run watch` exits non-zero if the job fails—treat that as a blocking issue, open a defect, and stop deployment promotion.
- `gh run view` (with `--json url`) prints the canonical run URL; copy it into the rehydration pack.

### Evidence expectations
- Open the job’s **Summary** tab once it succeeds. The Python script writes ingress URL, queue URL, DynamoDB idempotency/conversation_state/audit tables, log group, and CloudWatch Logs console deep links to `${GITHUB_STEP_SUMMARY}`—these are safe to paste because they’re derived identifiers, not secrets.
- Record the GitHub Actions run URL + pass/fail disposition in `REHYDRATION_PACK/RUNS/<RUN_ID>/C/TEST_MATRIX.md` alongside the summary confirmations that idempotency, conversation state, and audit records were observed (event_id + conversation_id). Paste the DynamoDB console links for each table.
- Capture the CloudWatch dashboard name (`rp-mw-<env>-ops`) and alarm names (`rp-mw-<env>-dlq-depth`, `rp-mw-<env>-worker-errors`, `rp-mw-<env>-worker-throttles`, `rp-mw-<env>-ingress-errors`) from the summary; if none appear, state “no dashboards/alarms surfaced”.
- Paste the routing + draft confirmation lines from the smoke summary (routing category/tags plus order_status_draft_reply presence and draft_replies count with safe fields only).
- If discovery falls back (missing CloudFormation outputs), capture the warning lines so reviewers can see which derived values were used, but never paste raw secret material.

## 7) Prod promotion checklist (no prod deploy without explicit go/no-go)

Only promote to prod with PM/lead approval recorded in the notes. Stop immediately if staging evidence is missing or stale.

### Checklist
- Record an explicit human go/no-go (name + timestamp) before any prod workflow is dispatched.
- Confirm staging deploy + staging E2E smoke are green and documented in the rehydration pack.
- Verify the prod change window + rollback owner are identified.
- Ensure Secrets Manager entries and required parameters for prod are current.
- Run `Deploy Prod Stack` only after go/no-go approval and capture the workflow run URL in the pack.
- After deploy, run `Prod E2E Smoke`; paste the summary output plus the prod smoke run URL into `REHYDRATION_PACK/RUNS/<RUN_ID>/A/TEST_MATRIX.md`.
- If either workflow fails, halt promotion and open/annotate an issue before retrying.

### PowerShell-safe commands
```powershell
# Deploy prod (requires explicit go/no-go)
$null = gh workflow run deploy-prod.yml --ref main
$prodDeployRunId = gh run list --workflow deploy-prod.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $prodDeployRunId --exit-status
$prodDeployUrl = gh run view $prodDeployRunId --json url --jq '.url'
$prodDeployUrl

# Prod E2E smoke validation
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
$null = gh workflow run prod-e2e-smoke.yml --ref main -f event-id=$eventId
$prodSmokeRunId = gh run list --workflow prod-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $prodSmokeRunId --exit-status
$prodSmokeUrl = gh run view $prodSmokeRunId --json url --jq '.url'
$prodSmokeUrl
```
Notes:
- Keep both run URLs plus the `${GITHUB_STEP_SUMMARY}` contents in the rehydration pack evidence tables.
- If prod deploy is intentionally deferred, record the decision and skip the commands.

## 8) Common causes (initial list)
- stale generated registries not committed
- accidental placeholder left in an INDEX-linked doc (doc hygiene)
- broken markdown link in `docs/INDEX.md`
- missing required rehydration pack file (manifest mismatch)
- accidental rename/delete in protected paths

### DynamoDB: `TypeError: Float types are not supported`
- **Symptom**: Worker (or local tests) fail with `TypeError: Float types are not supported`.
- **Root cause**: The boto3 DynamoDB serializer rejects Python `float` values (DynamoDB numbers must be serialized as `Decimal`).
- **Fix**: The worker sanitizes all records before `put_item`, recursively converting floats to `Decimal` (and stripping `NaN/Inf` to `None`).
- **How to verify in DEV/local**: run CI-equivalent checks (this includes the pipeline handler tests that validate float→Decimal sanitization):

```powershell
# Pick the correct region for your dev account/env (example uses us-east-2)
$env:AWS_REGION = "us-east-2"
$env:AWS_DEFAULT_REGION = $env:AWS_REGION
python scripts/run_ci_checks.py
```

---

## 9) If you cannot fix quickly
Escalate to PM by updating:
- `REHYDRATION_PACK/OPEN_QUESTIONS.md`
and include:
- failing job/step
- suspected cause
- attempted fixes
- proposed next actions

## 10) Seed Secrets Manager (dev/staging)
Optional workflow to upsert Secrets Manager entries without using the console.

- Workflow: `.github/workflows/seed-secrets.yml`
- Helper: `scripts/seed_secrets.py` (stdlib + AWS CLI; writes table to `$GITHUB_STEP_SUMMARY`)
- Role: `rp-ci-deploy` via OIDC (dev=151124909266, staging=260475105304)
- Region: `us-east-2`

### GitHub secrets required (repo Settings → Secrets and variables → Actions)
- `DEV_RICHPANEL_WEBHOOK_TOKEN`
- `DEV_RICHPANEL_API_KEY`
- `DEV_OPENAI_API_KEY`
- `STAGING_RICHPANEL_WEBHOOK_TOKEN`
- `STAGING_RICHPANEL_API_KEY`
- `STAGING_OPENAI_API_KEY`

### AWS secret IDs written (when the matching GitHub secret is present)
- `rp-mw/<env>/richpanel/webhook_token`
- `rp-mw/<env>/richpanel/api_key`
- `rp-mw/<env>/openai/api_key`

### How to run (PowerShell-safe)
```powershell
# dev
$null = gh workflow run seed-secrets.yml --ref main -f environment=dev
gh run watch --exit-status
gh run view --json url --jq '.url'

# staging
$null = gh workflow run seed-secrets.yml --ref main -f environment=staging
gh run watch --exit-status
gh run view --json url --jq '.url'
```
Notes:
- The script only writes secrets when the corresponding GitHub secret exists; missing inputs show as “skipped” in the job + step summary.
- Secret values are never echoed; only secret IDs and env var names appear in logs.