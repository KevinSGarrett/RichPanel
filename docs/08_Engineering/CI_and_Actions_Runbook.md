# CI and GitHub Actions Runbook (for Cursor Agents)

Last updated: 2025-12-29  
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

---

## 3) When GitHub Actions fails (red status)

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

## 4) Dev E2E smoke workflow

The “Dev E2E Smoke” workflow (`.github/workflows/dev-e2e-smoke.yml`) continuously validates the dev stack by sending a synthetic webhook and confirming the worker Lambda writes to DynamoDB.

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
- Copy the GitHub Actions run URL and the AWS console links emitted in the job summary into `REHYDRATION_PACK/RUNS/<RUN_ID>/C/TEST_MATRIX.md`.
- If the workflow fails, include the failure log excerpt plus the remediation plan in `RUN_SUMMARY.md`.

## 5) Staging E2E smoke workflow

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
- Open the job’s **Summary** tab once it succeeds. The Python script writes the ingress URL, queue URL, DynamoDB table, and CloudWatch Logs console deep links to `${GITHUB_STEP_SUMMARY}`—those are safe to paste because they’re derived identifiers, not secrets.
- Record the GitHub Actions run URL + pass/fail disposition in `REHYDRATION_PACK/RUNS/<RUN_ID>/C/TEST_MATRIX.md`.
- If discovery falls back (missing CloudFormation outputs), capture the warning lines so reviewers can see which derived values were used, but never paste raw secret material.

## 6) Common causes (initial list)
- stale generated registries not committed
- accidental placeholder left in an INDEX-linked doc (doc hygiene)
- broken markdown link in `docs/INDEX.md`
- missing required rehydration pack file (manifest mismatch)
- accidental rename/delete in protected paths

---

## 7) If you cannot fix quickly
Escalate to PM by updating:
- `REHYDRATION_PACK/OPEN_QUESTIONS.md`
and include:
- failing job/step
- suspected cause
- attempted fixes
- proposed next actions
