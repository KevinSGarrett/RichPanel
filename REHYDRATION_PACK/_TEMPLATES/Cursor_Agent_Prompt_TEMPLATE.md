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

## PR Health Check (REQUIRED before merge)
- PR link: <FILL_PR_LINK>
- Actions run link (CI): <PASTE_GITHUB_ACTIONS_RUN_URL or gh run view output>
- Codecov status (patch/project) if available: <status or "N/A">
- Bugbot status: <link or "quota exhausted — manual review provided">
  - If Bugbot quota is exhausted, include manual substitute review evidence (e.g., `python scripts/run_ci_checks.py --ci` output and/or `python -m compileall backend/src scripts` pass, plus a short findings summary).
- Required tests and how to run:
  - `python scripts/run_ci_checks.py --ci`
  - Optional manual check: `python -m compileall backend/src scripts`
- Record evidence in run artifacts (`RUN_REPORT.md`, `TEST_MATRIX.md`) with commands + outputs (no placeholders).

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