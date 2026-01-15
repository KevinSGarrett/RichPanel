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

## Risk classification (REQUIRED)

**Risk label:** `risk:R<#>-<level>`  
(Choose ONE: `risk:R0-docs`, `risk:R1-low`, `risk:R2-medium`, `risk:R3-high`, `risk:R4-critical`)

**Justification:**
- <Why this risk level applies based on blast radius, security impact, reversibility, etc.>

**Required gates per risk level:**
- R0: CI optional, no Bugbot/Codecov/Claude/E2E
- R1: CI required, Codecov advisory, Bugbot optional, Claude optional
- R2: CI + Codecov patch + Bugbot + Claude required
- R3: CI + Codecov (patch+project) + Bugbot (stale-rerun) + Claude (security prompt, stale-rerun) + E2E if outbound
- R4: All R3 gates + double-review + rollback plan + post-merge verification

See: `docs/08_Engineering/Quality_Gates_and_Risk_Labels.md` for complete reference.

---

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

**CI note:** In build mode, CI enforces minimum-populated run artifacts and expects **evidence**:
- Include **commands + outputs** in `RUN_REPORT.md` (not just ???ran tests???).
- CI also enforces **minimum non-empty line counts** for the latest run???s artifacts (see `python scripts/verify_rehydration_pack.py`).

## Required run artifacts (write to your agent folder)
Write to:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/`

Required files:
- `RUN_REPORT.md` (commands + outputs + proof; CI-enforced)
- `RUN_SUMMARY.md`
- `STRUCTURE_REPORT.md`
- `DOCS_IMPACT_MAP.md`
- `TEST_MATRIX.md`

Optional:
- `FIX_REPORT.md` (only if needed)

## Step-by-step
1) Read the referenced docs/paths.
2) Make the changes.
3) Run the planned tests and record evidence.
4) Update docs/maps/registry if needed.
5) Fill out the required run artifacts (especially `RUN_REPORT.md` with commands + outputs).

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
- [ ] Filled out required run artifacts in `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/` (including `RUN_REPORT.md`)
- [ ] Wrote agent summary (see schema above)

## PR Health Check (required for all PRs)

Before claiming a PR as "done", agents must complete the following health checks based on the risk level and document findings in `RUN_REPORT.md`.

### Risk label application (required first step)
- [ ] Applied exactly one risk label: `risk:R<#>-<level>`
  - Use: `gh pr edit <PR#> --add-label "risk:R<#>-<level>"`
- [ ] Documented risk justification in PR description and run report

### Gate lifecycle (two-phase approach)

**Phase A: Build & stabilize (local iteration)**
- [ ] Iterated locally, running `python scripts/run_ci_checks.py --ci` until green
- [ ] Only pushed to GitHub when diff was coherent (minimize CI/Codecov runs)

**Phase B: Gate execution (PR-level, once per stable state)**
- [ ] Applied `gates:ready` label when CI green and PR stable
- [ ] Triggered required gates (based on risk level)
- [ ] Waited for all gates to complete before declaring done

### CI validation (required for R1+)
- [ ] GitHub Actions `validate` check is green
- [ ] Local CI-equivalent passed: `python scripts/run_ci_checks.py --ci`

### Bugbot Review (required for R2+)
- [ ] Triggered Bugbot review via `@cursor review` or `bugbot run` PR comment
- [ ] Reviewed Bugbot findings in PR comments (`gh pr view <PR#> --comments`)
- [ ] **Action required**: Either fix all Bugbot findings in this run, OR document why each finding is deferred with a follow-up checklist item
- [ ] Documented Bugbot comment link in run report
- [ ] **If quota exhausted**: Documented "Bugbot quota exhausted; performed manual review" + findings in run report

### Codecov Status (required for R2+)
- [ ] Verified Codecov patch status (`codecov/patch`) is passing or acceptable (≥50% for R2+)
- [ ] Verified Codecov project status (`codecov/project`) is passing or acceptable (required for R3+)
- [ ] **Action required**: If Codecov flags coverage drop or insufficient patch coverage, either add tests to improve coverage OR document why coverage is acceptable as-is
- [ ] Documented Codecov status in run report

### Claude Review (required for R2+)
- [ ] **Required for**: R2 (medium), R3 (high), R4 (critical)
- [ ] **Optional for**: R0 (docs), R1 (low)
- [ ] Triggered Claude review:
  - Option 1: `gh pr comment <PR#> -b '@claude review'` (if supported)
  - Option 2: Manual review using PR diff + Claude API/web interface (if Anthropic key unavailable)
- [ ] **For R3/R4**: Used security-focused prompt (auth, PII, input validation, secrets, error leakage)
- [ ] Documented Claude verdict (PASS/CONCERNS/FAIL) and link in run report
- [ ] **Action required**: Fixed concerns or documented waivers with justification
- [ ] **If API unavailable**: Applied `waiver:active` label + documented manual review process

### E2E Proof (required for R3/R4 or when touching outbound/automation)
- [ ] **Required when**: Changes touch outbound integrations (Richpanel API, Shopify, ShipStation, email/SMS) or automation logic, OR risk level is R3/R4
- [ ] Run appropriate E2E smoke test: `dev-e2e-smoke.yml`, `staging-e2e-smoke.yml`, or `prod-e2e-smoke.yml`
- [ ] Record E2E run URL + summary in `TEST_MATRIX.md` and `RUN_REPORT.md`
- [ ] **Action required**: If E2E test fails, fix the issue before merging

### Staleness check (required for R2+)
- [ ] Verified no new commits landed after Bugbot/Claude review
- [ ] If new commits occurred after gates: re-ran required gates and updated `gates:stale` → `gates:passed`

### Wait-for-green (mandatory for all PRs)
- **Do not declare the run complete** or enable auto-merge until Bugbot (if required) and Codecov (if required) have finished and are green (or a documented fallback is recorded).
- After triggering Bugbot and pushing commits, **poll checks every 120–240s** until neither `gh pr checks <PR#>` nor the status rollup shows pending/in-progress contexts for Codecov or Bugbot.
- Sample PowerShell-safe loop (adjust sleep as needed):
```powershell
$pr = <PR#>
do {
  gh pr checks $pr
  Start-Sleep -Seconds (Get-Random -Minimum 120 -Maximum 240)
} while (gh pr checks $pr | Select-String -Pattern 'Pending|In progress|Queued')
```
- If Bugbot quota is exhausted, record “quota exhausted; performed manual review” in `RUN_REPORT.md` and continue waiting for Codecov to complete before merging.
### Final gate compliance checklist
- [ ] Applied `gates:passed` label when all required gates completed successfully
- [ ] All required gates satisfied per risk level (see Risk classification section above)
- [ ] All evidence links recorded in run report (no placeholders)
- [ ] Waivers documented (if any) with `waiver:active` label + justification in PR description and run report

**Gate rule**: A PR cannot be merged without:
1. Exactly one risk label (R0-R4)
2. All required gates for that risk level satisfied
3. Evidence documented in run report
4. Gates non-stale (or re-run after new commits)
5. `gates:passed` label applied
