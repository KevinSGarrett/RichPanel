# Cursor Agent Prompt

**Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`  
**Agent:** Agent A | Agent B | Agent C  
**Task ID(s):** `<TASK-###, TASK-###>`

---

## Model + MAX mode + Cycle (REQUIRED)
- **Model used:** `<model-name>` (see `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`)
- **MAX mode:** ON | OFF
- **Cycle:** 1× | 2× | 3× | 4×

**Note:** Always check Cursor's model picker for the current model list. If you can't find the exact model name, pick the closest family (see catalog).

---

## Context (read first)
- Current goal: <FILL_ME>
- Relevant docs/paths:
  - `<PATH_1>`
  - `<PATH_2>`
  - `<PATH_3>` (optional)

## Objective
<FILL_ME>

## Deliverables (explicit)
- [ ] <DELIVERABLE_1>
- [ ] <DELIVERABLE_2>
- [ ] <DELIVERABLE_3> (optional)

## Tests / evidence required
- Tests to run: <FILL_ME>
- Evidence location:
  - `qa/test_evidence/<RUN_ID>/` (or CI link)

## Required run artifacts (write to your agent folder)
Write to:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/`

Required files:
- `RUN_REPORT.md` — **MUST replace all placeholders** (commands + outputs, tests, diffstat, files changed)
- `RUN_SUMMARY.md` — **MUST replace all placeholders**
- `STRUCTURE_REPORT.md` — **MUST replace all placeholders**
- `DOCS_IMPACT_MAP.md` — **MUST replace all placeholders**
- `TEST_MATRIX.md` — **MUST replace all placeholders**

Optional:
- `FIX_REPORT.md` (only if needed)

**CRITICAL**: CI will fail if your run artifacts contain template placeholders like `<FILL_ME>`, `RUN_<YYYYMMDD>_<HHMMZ>`, `<PATH_1>`, etc. All placeholders MUST be replaced with actual values before completing the run.

## Step-by-step
1) Read the referenced docs/paths.
2) Make the changes.
3) Run the planned tests and record evidence.
4) Update docs/maps/registry if needed.
5) Fill out the required run artifacts.

---

## Agent summary schema (REQUIRED for rehydration)

When completing work, the agent **must** provide a structured summary to enable seamless handoff and prevent "already done" loops.

### Prompt set fingerprint (REQUIRED)

Agents must include the **prompt set fingerprint** in their summary.

Source:
- Run `python scripts/verify_agent_prompts_fresh.py` (or `python scripts/run_ci_checks.py`) and copy the line:
  - `[INFO] Prompt set fingerprint: <sha256>`

### Required sections

**1. Work completed**
- List of files changed (with brief descriptions)
- Tests run and results
- Evidence artifacts created

**2. Merge state**
- Current branch name
- Worktree location (verify with `pwd`)
- PR number (if created)
- PR status (open/merged/closed)
- Last commit SHA on this branch
- Prompt set fingerprint (from `verify_agent_prompts_fresh.py` / CI output)

**3. What's NOT done (if applicable)**
- Tasks explicitly deferred
- Known issues or limitations
- Follow-up tasks needed

**4. Handoff notes**
- Anything the next agent/PM needs to know
- Where to find key artifacts
- Any blockers or dependencies

### Format

```markdown
## Agent Summary

### Work completed
- Changed `<file1>`: <description>
- Changed `<file2>`: <description>
- Ran: `<test-command>` → <result>
- Evidence: `<path-to-artifact>`

### Merge state
- Branch: `<branch-name>`
- Worktree: `<pwd-output>`
- PR: #<number> (<open|merged|closed>)
- Last commit: `<sha>`
- Prompt set fingerprint: `<sha256>`

### Not done
- <item-1>
- <item-2>

### Handoff notes
- <note-1>
- <note-2>
```

### Why this matters

Without this summary:
- Next agent may redo completed work ("already done" loop)
- PM may lose track of merge state
- CI failures are hard to debug (wrong worktree, wrong branch)
- Rehydration takes longer and wastes tokens

With this summary:
- Clear handoff between agents
- No ambiguity about what's merged vs. what's pending
- Easy to recover from interruptions
- Fast rehydration from summaries

---

## Pre-commit checklist

Before pushing your branch:

- [ ] Verified `pwd` shows the correct worktree (usually `C:\RichPanel_GIT`)
- [ ] Verified `git branch --show-current` shows the correct branch
- [ ] Ran `python scripts/run_ci_checks.py` locally (CI-equivalent checks)
- [ ] Updated `REHYDRATION_PACK/GITHUB_STATE.md` if creating/merging PRs
- [ ] Filled out required run artifacts in `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/`
- [ ] Wrote agent summary (see schema above)

---

## PR Health Check (REQUIRED before merge)

Every PR must pass the following health checks before merge. Document results in your run artifacts.

### 1. CI Status
- [ ] All CI checks are green (`.github/workflows/ci.yml`)
- [ ] Recorded CI run URL in run artifacts
- [ ] Fixed any CI failures (see `docs/08_Engineering/CI_and_Actions_Runbook.md` section 4)

### 2. Codecov Status
- [ ] Codecov patch status checked (target: ≥50% on changed lines)
- [ ] Codecov project status checked (no >5% coverage drop)
- [ ] Recorded Codecov status in run artifacts
- [ ] If coverage issues exist, either:
  - Added tests to meet threshold, OR
  - Documented why coverage gap is acceptable

### 3. Bugbot Review
- [ ] Triggered Bugbot via PR comment: `@cursor review` or `bugbot run`
- [ ] Recorded Bugbot review output in run artifacts
- [ ] Addressed all Bugbot findings OR documented why findings are false positives
- [ ] If Bugbot quota exhausted, performed manual code review and documented findings

**Commands (PowerShell-safe):**
```powershell
# Get PR number for current branch
$pr = gh pr view --json number --jq '.number'

# Trigger Bugbot
gh pr comment $pr -b '@cursor review'

# View PR status checks
gh pr view $pr --json statusCheckRollup --jq '.statusCheckRollup'

# Get CI run URL
gh run list --branch (git branch --show-current) --workflow ci.yml --limit 1 --json url --jq '.[0].url'
```

### 4. E2E Testing (when automation/outbound logic is touched)
- [ ] Identified if changes touch automation/outbound paths
- [ ] Ran appropriate E2E smoke test(s):
  - Dev: `gh workflow run dev-e2e-smoke.yml`
  - Staging: `gh workflow run staging-e2e-smoke.yml` (after deploy)
  - Prod: `gh workflow run prod-e2e-smoke.yml` (only with PM approval)
- [ ] Captured E2E run URLs and summary outputs in run artifacts
- [ ] All E2E tests passed OR failures documented with remediation plan

**See:** `docs/08_Engineering/E2E_Test_Runbook.md` for detailed E2E testing procedures.

### 5. Evidence Capture
All PR health check results must be captured in:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/RUN_REPORT.md` (PR Health Check section)
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md` (E2E evidence)

**No placeholders allowed** — CI will fail if template placeholders remain in run artifacts.
