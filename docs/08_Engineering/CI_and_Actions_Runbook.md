# CI and GitHub Actions Runbook (for Cursor Agents)

Last updated: 2025-12-29  
Status: Canonical

This runbook defines how agents must keep CI green and how to self-fix when GitHub Actions fails.

---

## 1) CI contract
A change is not considered “done” until:

- local CI-equivalent checks pass (`python scripts/run_ci_checks.py`)
- GitHub Actions checks are green (unless explicitly waived by PM)

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

## 4) Common causes (initial list)
- stale generated registries not committed
- accidental placeholder left in an INDEX-linked doc (doc hygiene)
- broken markdown link in `docs/INDEX.md`
- missing required rehydration pack file (manifest mismatch)
- accidental rename/delete in protected paths

---

## 5) If you cannot fix quickly
Escalate to PM by updating:
- `REHYDRATION_PACK/OPEN_QUESTIONS.md`
and include:
- failing job/step
- suspected cause
- attempted fixes
- proposed next actions
