# CI and GitHub Actions Runbook (for Cursor Agents)

Last updated: 2026-01-16  
Status: Canonical

This runbook defines how agents must keep CI green and how to self-fix when GitHub Actions fails.

---

## 1) CI contract
A change is not considered “done” until:

- local CI-equivalent checks pass (`python scripts/run_ci_checks.py`)
- GitHub Actions checks are green (unless explicitly waived by PM)

### What runs in CI (ci.yml)
Every PR automatically runs:

1. Set up Python 3.11 + install tooling (`black`, `mypy`, `ruff`, `coverage`)
2. Set up Node.js 20 with npm cache for `infra/cdk`
3. `npm ci`, `npm run build`, and `npx cdk synth` in `infra/cdk`
4. `python scripts/run_ci_checks.py --ci` for repo-wide policy + hygiene validation
5. `ruff check backend/src scripts` (advisory; continue-on-error)
6. `black --check backend/src scripts` (advisory; continue-on-error)
7. `mypy --config-file mypy.ini` (advisory; continue-on-error)
8. `coverage run -m unittest discover -s scripts -p "test_*.py"` + `coverage xml`
9. Upload to Codecov using `codecov/codecov-action@v4` with `fail_ci_if_error: false`
10. Upload `coverage.xml` as artifact with 30-day retention

Steps 1-4 are blocking; lint (5-7) and coverage (8-10) are advisory but should be addressed over time. See Section 9 (Codecov) and Section 10 (Lint enforcement) for phased rollout plans.

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

## 4) Risk labels and gate requirements (NewWorkflows)

**Every PR must have exactly one risk label** that determines which quality gates are required before merge.

### 4.0.1 Risk label taxonomy

Apply exactly one of these labels to every PR (use `gh pr edit <PR#> --add-label "<label>"`):

- **`risk:R0-docs`** — Docs-only / non-functional changes
  - Examples: docs edits, markdown formatting, typos, README updates
  - Gates: CI optional (if repo requires it, must pass); Bugbot/Codecov/Claude not required

- **`risk:R1-low`** — Low-risk, localized changes
  - Examples: small refactors, non-critical bugfixes, logging tweaks, UI copy changes
  - Gates: CI required; Codecov advisory; Bugbot optional (required if critical zones touched); Claude optional

- **`risk:R2-medium`** — Behavior changes or non-trivial logic
  - Examples: new endpoints, automation routing changes, classifier threshold updates, caching changes, schema changes
  - Gates: CI required; Codecov patch required; Bugbot required; Claude semantic review required

- **`risk:R3-high`** — High blast radius or security-sensitive
  - Examples: auth/permissions changes, PII handling, webhooks, payment/order logic, background jobs, infra runtime changes
  - Gates: CI required; Codecov patch + project; Bugbot required (stale-rerun); Claude required (security prompt); E2E proof required if outbound/automation

- **`risk:R4-critical`** — Production emergency / security incident
  - Examples: actively exploited vulnerabilities, incident mitigation, key rotation, data corruption fixes
  - Gates: All R3 gates + double-review strategy + explicit rollback plan + post-merge verification

**Critical zones** (auto-upgrade to R2 minimum):
- Any file under `backend/`
- Automation/routing logic
- Webhook handlers
- Anything touching: secrets, auth, PII, outbound requests, persistence/data migration

### 4.0.2 Gate lifecycle labels (optional but recommended)

Use these labels to track gate status through the PR workflow:

- **`gates:ready`** — PR is stable (CI green, diff coherent) and ready to run heavy gates (Bugbot/Claude/Codecov)
- **`gates:running`** — Gate workflows are currently in-flight
- **`gates:passed`** — Required gates completed successfully for current PR state
- **`gates:stale`** — New commits landed after gates ran; must re-run gates before merge

**Staleness rule:** If a PR receives new commits after Bugbot/Claude review or after `gates:passed` label was applied, gates become stale. The PR must return to `gates:stale` status and re-run required gates.

### 4.0.3 Risk labels + seeded gate labels

Risk and gate labels are seeded via a workflow so every repo has the same taxonomy.

#### How to trigger label seeding
- Actions UI: run workflow `.github/workflows/seed-gate-labels.yml`
- PowerShell-safe CLI:
```powershell
gh workflow run seed-gate-labels.yml --ref main
```

#### PowerShell-safe label examples (risk + gate)
```powershell
# Apply exactly one risk label (required)
gh pr edit <PR_NUMBER> --add-label "risk:R0-docs"
gh pr edit <PR_NUMBER> --add-label "risk:R1-low"
gh pr edit <PR_NUMBER> --add-label "risk:R2-medium"
gh pr edit <PR_NUMBER> --add-label "risk:R3-high"
gh pr edit <PR_NUMBER> --add-label "risk:R4-critical"

# Trigger optional Claude review
gh pr edit <PR_NUMBER> --add-label "gate:claude"
```

#### How to trigger Claude review (optional)
Claude review runs only when the PR has the `gate:claude` label.
If `ANTHROPIC_API_KEY` is missing, the workflow skips with a log line and does not fail.

### 4.0.4 Cost-aware gate strategy (two-phase approach)

**Phase A: Build & stabilize (local iteration)**
- Agent iterates locally
- Runs `python scripts/run_ci_checks.py --ci` until green
- Commits locally as needed
- Pushes to GitHub only when diff is coherent (reduces CI/Codecov cost)

**Phase B: Gate execution (PR-level, once per stable state)**
- When CI is green and PR is stable, apply label: `gates:ready`
- Heavy gates run once:
  - Bugbot (if required by risk level)
  - Claude review (if required by risk level)
  - Codecov gating (if required by risk level)
- This avoids running expensive AI reviews on every micro-commit

---

## 5) PR Health Check (required before merge)

Every PR must pass the following health checks before being considered "done" and merged. Document all findings in `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/RUN_REPORT.md`.

### 5.0 Wait-for-green gate (mandatory)
- **No “done” until green:** Do not declare a run complete or enable auto-merge until Codecov and Bugbot checks have finished and are green (or an explicitly documented fallback is recorded).
- **Wait loop:** After pushing and triggering Bugbot, poll checks every 120–240 seconds until the PR status rollup (and `gh pr checks <PR#>`) shows Codecov + Bugbot contexts completed/green.
  ```powershell
  $pr = <PR#>
  do {
    gh pr checks $pr
    Start-Sleep -Seconds (Get-Random -Minimum 120 -Maximum 240)
  } while (gh pr checks $pr | Select-String -Pattern 'Pending|In progress|Queued')
  ```
- **Bugbot quota exhausted:** Record "Bugbot quota exhausted; performed manual review" in `RUN_REPORT.md`, perform a manual diff review (focus on risk areas/tests touched), and capture findings/deferrals. You must still wait for Codecov to finish and be green before merging.

### 5.1 Bugbot review

**Requirement:** All PRs must receive a Bugbot review (or explicit fallback if quota exceeded).

#### How to trigger Bugbot (mention-only mode)
Post a trigger comment on the PR:
```powershell
# Using PR number
gh pr comment <PR#> -b '@cursor review'
# or
gh pr comment <PR#> -b 'bugbot run'

# Using current branch (infers PR)
gh pr comment (gh pr view --json number --jq '.number') -b '@cursor review'
```

Alternative: Use workflow dispatch (see Section 3 for details).

#### How to view Bugbot output
```powershell
# View all PR comments (including Bugbot output)
gh pr view <PR#> --comments

# Filter for Bugbot comments (if many comments exist)
gh pr view <PR#> --json comments --jq '.comments[] | select(.author.login=="cursor-bot" or .body | contains("Bugbot")) | {author: .author.login, body: .body}'
```

#### Action required
- **If Bugbot flags issues**: Either fix them in this run OR document each deferred finding with a follow-up checklist item in `REHYDRATION_PACK/05_TASK_BOARD.md` or `docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md`
- **If quota exceeded**: Document "Bugbot quota exceeded; performed manual code review" and list manual review findings

### 5.2 Codecov status verification

**Requirement:** Verify Codecov patch and project status checks are passing or acceptable.

#### How to view Codecov status
```powershell
# View PR checks (includes Codecov statuses)
gh pr view <PR#> --json statusCheckRollup --jq '.statusCheckRollup[] | select(.context | contains("codecov")) | {context: .context, state: .state, description: .description, targetUrl: .targetUrl}'

# View full PR status including Codecov
gh pr checks <PR#>
```

#### Codecov thresholds (current)
- **Patch coverage**: ≥50% (±10% threshold)
- **Project coverage**: must not drop >5% from base branch

#### Action required
- **If patch coverage is low**: Add tests to cover new/changed lines OR document why coverage is acceptable (e.g., "integration test planned for staging")
- **If project coverage drops**: Investigate which files lost coverage; add tests or document rationale

#### Fallback if Codecov is unavailable
If Codecov is not configured or failing to upload:
- Download the `coverage-report` artifact from the CI run
- Review `coverage.xml` locally
- Document: "Codecov unavailable; reviewed coverage.xml directly (X% patch coverage)"

### 5.3 Claude review (Semantic Review Agent)

**Requirement:** Claude semantic review is required for R2+ PRs (medium, high, critical risk).

Claude review provides a semantic/correctness/security-focused review of the diff, complementing Bugbot's bug detection.

#### When Claude review is required

- **R0/R1**: Optional (not required unless uncertainty exists)
- **R2 (medium)**: Required once on stable diff
- **R3 (high)**: Required with security-focused prompt; rerun if significant changes occur after review
- **R4 (critical)**: Required + double-review strategy (Claude + independent LLM review, e.g., AM deep review)

#### How to trigger Claude review

**Option 1: GitHub comment (if supported by your setup)**
```powershell
gh pr comment <PR#> -b '@claude review'
```

**Option 2: Manual Claude API call (fallback when Anthropic key is missing)**
- If Anthropic API key is not configured in your environment, you must perform manual review:
  1. Download the PR diff: `gh pr diff <PR#> > pr_diff.txt`
  2. Conduct manual code review focusing on:
     - Correctness and logic errors
     - Security implications (especially for R3/R4)
     - Edge cases and error handling
     - Integration correctness
  3. Document review findings in run report with section: "Claude review fallback (manual)"
  4. Apply waiver label: `waiver:active` and document the waiver in PR description

**Option 3: External Claude review (via ChatGPT or Claude web interface)**
- Copy the PR diff and paste into a Claude conversation
- Use this prompt for R2:
  ```
  Please review this code change for correctness, security, and potential bugs.
  Focus on: logic errors, edge cases, error handling, integration issues.
  ```
- Use this prompt for R3/R4 (security-focused):
  ```
  Please perform a security-focused code review of this change.
  Pay special attention to: authentication, authorization, PII handling,
  input validation, SQL injection, XSS, secrets exposure, rate limiting,
  outbound request safety, error information leakage.
  ```
- Copy the review output and paste into run report

#### How to view Claude review output

If Claude posts to GitHub:
```powershell
# View PR comments (including Claude output)
gh pr view <PR#> --comments

# Filter for Claude comments
gh pr view <PR#> --json comments --jq '.comments[] | select(.author.login=="claude-bot" or .body | contains("Claude")) | {author: .author.login, body: .body}'
```

#### Action required

- **If Claude flags concerns**: Either fix them in this run OR document each item with justification/waiver
- **If Claude verdict is PASS**: Record the verdict and link in run report
- **If Claude verdict is FAIL**: Fix blocking issues before merge; waivers require PM approval
- **If Anthropic key is missing**: Document manual review process and findings; apply `waiver:active` label

#### Evidence requirements

Document in run report:
- Claude triggered: yes/no (or "manual fallback")
- Link to Claude output (or "manual review recorded")
- Verdict: PASS/CONCERNS/FAIL (or "manual: no blocking issues")
- Actions taken (fixes or waivers with justification)

---

### 5.4 E2E proof (when applicable)

**Requirement:** When changes touch outbound integrations or automation logic, E2E smoke test must pass.

#### When E2E proof is mandatory
- Changes to `backend/src/lambda_handlers/worker/handler.py` (automation execution)
- Changes to `backend/src/richpanel_middleware/integrations/` (Richpanel, Shopify, ShipStation clients)
- Changes to webhook ingestion or event handling
- Changes to routing logic that affects automation triggers

#### How to run E2E smoke tests
**Dev environment:**
```powershell
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run dev-e2e-smoke.yml --ref <branch-name> -f event-id=$eventId
gh run watch --exit-status
gh run view --json url --jq '.url'
```

**Staging environment** (after staging deploy):
```powershell
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run staging-e2e-smoke.yml --ref main -f event-id=$eventId
$runId = gh run list --workflow staging-e2e-smoke.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $runId --exit-status
gh run view $runId --json url --jq '.url'
```

#### Action required
- **If E2E test passes**: Record run URL + summary in `TEST_MATRIX.md` and `RUN_REPORT.md`
- **If E2E test fails**: Fix the issue before merging; do not defer E2E failures

#### Evidence expectations
Capture in `TEST_MATRIX.md`:
- GitHub Actions run URL
- Job summary (ingress URL, queue URL, DynamoDB tables, CloudWatch Logs)
- Confirmation that idempotency, conversation state, and audit records were written
- Routing result (category/tags)
- Draft reply confirmation (count, safe fields only)

### 5.5 PR Health Check CLI reference card

Quick reference for all health checks:
```powershell
# 0. Apply risk label (required)
gh pr edit <PR#> --add-label "risk:R2-medium"  # Choose appropriate risk level

# 1. Trigger Bugbot
gh pr comment <PR#> -b '@cursor review'

# 2. View Bugbot output
gh pr view <PR#> --comments

# 3. View Codecov status
gh pr checks <PR#>

# 4. Trigger Claude review (if required for R2+)
# Option 1: GitHub comment (if supported)
gh pr comment <PR#> -b '@claude review'
# Option 2: Manual review (if Anthropic key missing)
gh pr diff <PR#> > pr_diff.txt
# Then review manually and document in run report

# 5. Run E2E smoke (dev) - if required for R3/R4 or outbound changes
$eventId = "evt:" + (Get-Date -Format 'yyyyMMddHHmmss')
gh workflow run dev-e2e-smoke.yml --ref <branch> -f event-id=$eventId
gh run watch --exit-status

# 6. View E2E results
gh run view --json url --jq '.url'

# 7. Apply gate status labels as workflow progresses
gh pr edit <PR#> --add-label "gates:ready"   # When PR is stable
gh pr edit <PR#> --add-label "gates:passed"  # When all gates green
```

---

## 6) When GitHub Actions fails (red status)

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

## 7) Dev E2E smoke workflow

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

### DEV proof window: enabling outbound writes (dev-only)
- Purpose: temporarily enable outbound writes on `rp-mw-dev-worker` for PASS_STRONG proofs, with automatic revert.
- Step 1: run `set-runtime-flags.yml` with `safe_mode=false` and `automation_enabled=true`.
- Step 2: run `set-outbound-flags.yml` with `action=enable`, `auto_revert=true`, `revert_after_minutes=30` (recommended; max 55; inputs like `08` are accepted but prefer plain numbers such as `8`).
- After the proof, either let auto-revert run or dispatch `set-outbound-flags.yml` with `action=disable` immediately.
- Reminder: DEV only—never use this workflow for staging or prod.

#### CLI proof (real Richpanel tokens + test tag)
- Use when you need unambiguous DEV evidence with real Richpanel tokens and a real ticket.
- PowerShell-safe example (replace placeholders):
```powershell
$runId = "RUN_20260112_0259Z"
$ticketId = "<richpanel-ticket-id-or-number>"
python scripts/dev_e2e_smoke.py `
  --env dev `
  --region us-east-2 `
  --stack-name RichpanelMiddleware-dev `
  --idempotency-table rp_mw_dev_idempotency `
  --wait-seconds 90 `
  --profile <aws-profile> `
  --ticket-id $ticketId `
  --run-id $runId `
  --apply-test-tag `
  --proof-path "REHYDRATION_PACK/RUNS/$runId/B/e2e_outbound_proof.json"
```
- You may use `--ticket-number` instead of `--ticket-id`. `--apply-test-tag` requires one of them.
- The script:
  - sends the webhook and waits for idempotency/state/audit records,
  - applies `mw-smoke:<RUN_ID>` as a tag via Richpanel API,
  - fetches pre/post ticket status + tags and records tag deltas + updated_at delta,
  - writes a PII-safe proof JSON (command used, criteria, Dynamo links, tag verification).

##### Order-status scenario (DEV proof)
PowerShell-safe example (replace placeholders):
```powershell
$runId = "RUN_20260113_0433Z"
$ticketNumber = "<dev-richpanel-ticket-number>"
python scripts/dev_e2e_smoke.py `
  --env dev `
  --region us-east-2 `
  --stack-name RichpanelMiddleware-dev `
  --wait-seconds 120 `
  --profile <aws-profile> `
  --ticket-number $ticketNumber `
  --confirm-test-ticket `
  --diagnose-ticket-update `
  --run-id $runId `
  --scenario order_status `
  --proof-path "REHYDRATION_PACK/RUNS/$runId/B/e2e_outbound_proof.json"
```
- Use a **real DEV ticket** (ID or number); the scenario fails fast without one.
- PASS_STRONG criteria: webhook accepted; idempotency + state + audit records observed; routing intent is order-status; **ticket status resolved/closed AND reply evidence from middleware** (message_count delta > 0, `last_message_source=middleware`, or status_changed metadata from the middleware reply); no skip/escalation tags (`mw-skip-*`, `route-email-support-team`, `mw-escalated-human`). PASS_WEAK only allowed when Richpanel refuses status changes but middleware still tags successfully; classification is recorded in `result.classification`.
- Proof JSON must include scenario name, classification, pass criteria details, Dynamo evidence (idempotency/state/audit), pre/post ticket status + tags, message_count delta / last_message_source, and PII scan result.
- Optional diagnostic (recommended): include `--diagnose-ticket-update --confirm-test-ticket` to try candidate Richpanel update schemas (status/state/closed/comment) against the target ticket; diagnostics are PII-safe (redacted paths, ticket fingerprint only). The working schema today is `{\"ticket\": {\"state\": \"closed\"}}` (status/state at top level are rejected).

#### PII-safe proof JSON requirements
Proof JSON must never contain raw ticket IDs or Richpanel API paths that embed IDs.
- **Fingerprints only:** Ticket IDs are hashed to `ticket_id_fingerprint` (12-char SHA256 prefix).
- **Redacted paths:** API paths use `path_redacted` with `<redacted>` placeholders (e.g., `/v1/tickets/<redacted>/add-tags`).
- **Safety assertion:** The script scans the proof JSON before writing and fails if it detects `%40`, `mail.`, `%3C`, `%3E`, or `@`.

### Evidence expectations
- Copy the GitHub Actions run URL and the job summary block (ingress URL, queue URL, DynamoDB tables, log group, CloudWatch Logs) into `REHYDRATION_PACK/RUNS/<RUN_ID>/C/TEST_MATRIX.md`.
- Record the explicit confirmations from the summary that idempotency, conversation state, and audit records were written (event_id + conversation_id observed) and link the DynamoDB consoles for each table.
- Capture the CloudWatch dashboard name (`rp-mw-<env>-ops`) and alarm names (`rp-mw-<env>-dlq-depth`, `rp-mw-<env>-worker-errors`, `rp-mw-<env>-worker-throttles`, `rp-mw-<env>-ingress-errors`) from the summary; if the stack is missing any, state “no dashboards/alarms surfaced”.
- Paste the smoke summary lines that confirm routing category/tags and the order_status_draft_reply plan + draft_replies count (safe fields only; no message bodies).
- For order_status, note classification (PASS_STRONG vs PASS_WEAK) plus the evidence that status changed to resolved/closed and reply evidence was observed (message_count delta or last_message_source=middleware).
- If the workflow fails, include the failure log excerpt plus the remediation plan in `RUN_SUMMARY.md`.
- For CLI proofs, attach the proof JSON path (e.g., `REHYDRATION_PACK/RUNS/<RUN_ID>/B/e2e_outbound_proof.json`), the exact command used, and confirm that `mw-smoke:<RUN_ID>` appears in tags_added with updated_at delta > 0.

## 8) Staging E2E smoke workflow

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

## 9) Prod promotion checklist (no prod deploy without explicit go/no-go)

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

## 10) Common causes (initial list)
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

## 11) Codecov coverage reporting and gating

### Current state (2026-01-11)
With `CODECOV_TOKEN` configured as a GitHub repository secret, coverage is automatically uploaded on every CI run.

**Coverage workflow:**
1. CI runs `coverage run -m unittest discover -s scripts -p "test_*.py"` followed by `coverage xml`
2. `coverage.xml` is uploaded to Codecov using `codecov/codecov-action@v4` (advisory; does not block CI)
3. `coverage.xml` is also uploaded as a GitHub Actions artifact (`coverage-report`) with 30-day retention for debugging

**Status checks configured in codecov.yml:**
- **Project status**: requires coverage not to drop by more than 5% compared to base branch
- **Patch status**: requires at least 50% coverage on new/changed lines (±10% threshold)
- Both checks use `target: auto` and generous thresholds to avoid breaking PRs on day 1

### Operational plan (phased rollout)

**Phase 1: Observation (current)**
- Codecov uploads on every PR but does not block merges
- CI step uses `fail_ci_if_error: false`
- Monitor Codecov PR comments and status checks for 2-3 PRs to validate behavior

**Phase 2: Soft enforcement (after 2-3 green runs)**
- Once Codecov is reliably uploading and posting comments without false positives:
  1. Change `fail_ci_if_error: false` to `fail_ci_if_error: true`
  2. Add `codecov/patch` and optionally `codecov/project` as **required status checks** in branch protection rules
- This makes coverage gating a hard requirement without breaking existing PRs

**Phase 3: Tighten targets (incremental)**
- After Phase 2 is stable, gradually increase coverage targets in `codecov.yml`:
  - Patch target: 50% → 60% → 70%
  - Project threshold: 5% → 3% → 1%
- Make changes incrementally and observe impact before tightening further

### Codecov verification (per-PR)

Assuming `CODECOV_TOKEN` is configured and CI is green, use this checklist to verify Codecov behavior on a PR:

1. Identify the latest `CI` workflow run for the PR branch and copy its URL
2. In the `CI` run, confirm the **"Upload coverage to Codecov"** step completed without error
3. On the PR's **Checks** surface, confirm Codecov statuses appear (e.g., `codecov/project`, `codecov/patch`)

### Troubleshooting Codecov failures

**Coverage upload fails (401/403)**
- Verify `CODECOV_TOKEN` is set in GitHub repository secrets

**Coverage.xml missing or empty**
- Verify `coverage run -m unittest discover -s scripts -p "test_*.py"` succeeded in CI logs
- Check that `coverage xml` ran without errors
- Download the `coverage-report` artifact from GitHub Actions to inspect the raw XML

---

## 12) Lint/Type enforcement roadmap

### Current state (2026-01-11)
Linters (ruff, black, mypy) run in CI but use `continue-on-error: true` (advisory). They do **not** block PR merges.

**Lint status snapshot:**
- **Ruff**: ~4 issues (line length E501, unused imports F401, unused variables F841)
- **Black**: ~30+ files would be reformatted
- **Mypy**: 11 errors in 3 files (union-attr, arg-type, return-value)

### Operational plan (phased enforcement)

**Phase 1: Advisory (current)**
- All lint steps run but do not block CI
- Developers can see lint warnings in CI logs and optionally fix

**Phase 2: Fix + enforce (target: after 2-3 green PRs)**
- Dedicated PR to auto-fix black formatting: `black backend/src scripts`
- Dedicated PR to fix ruff issues: `ruff check --fix backend/src scripts`
- Once both pass cleanly, remove `continue-on-error: true` from those steps to make them blocking

**Phase 3: Mypy enforcement (incremental)**
- Address mypy errors file-by-file (envelope.py, client.py, order_lookup.py)
- Once mypy passes, remove `continue-on-error: true` to make it blocking
- Consider adding mypy to pre-commit hooks

### Tracking
- When Phase 2 is complete, update this section and `ci.yml` to reflect blocking status
- File issues for any recurring lint failures that block progress

---

## 13) If you cannot fix quickly
Escalate to PM by updating:
- `REHYDRATION_PACK/OPEN_QUESTIONS.md`
and include:
- failing job/step
- suspected cause
- attempted fixes
- proposed next actions

## 14) Seed Secrets Manager (dev/staging)
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
