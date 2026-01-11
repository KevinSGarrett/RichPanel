# Archive — snapshot of `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`

Archived at run creation for `RUN_20260110_1622Z`.

---

# Current Cursor Agent Prompts (build mode)

This file must contain **only the currently active prompts** for the current run/cycle.
prompt-repeat-override: true

**⚠️ REQUIRED IN EVERY PROMPT:** Model + MAX mode + Cycle metadata (see below)

---

## Model + MAX mode + Cycle (REQUIRED)

**Every prompt set MUST include this section for each agent:**

```markdown
## Model + MAX mode + Cycle
- **Model used:** <model-name> (see REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md)
- **MAX mode:** ON | OFF
- **Cycle:** 1× | 2× | 3× | 4×
```

**Why this matters:**
- Prevents drift where some prompts omit guidance
- Makes prompt archives searchable by model
- Helps PM/agents understand context budget and review depth

**Source of truth:**
- Model list: `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`
- Active model picker: Cursor IDE model picker (always check there first)

---

## Workflow (starting a new run)

If you are starting a new run:
1) Create a run folder skeleton:
```bash
python scripts/new_run_folder.py --now
```
2) Paste the active prompts here (Agent A/B/C), including the **Model + MAX mode + Cycle** section for each agent
3) Run agents sequentially to avoid merge conflicts
4) When the cycle ends, archive the prior prompt text under `REHYDRATION_PACK/RUNS/<RUN_ID>/C/`

---

## Archive pointer (do not edit)
- Prior prompt content for `RUN_20260103_2300Z` was archived to:
  - `REHYDRATION_PACK/RUNS/RUN_20260103_2300Z/C/AGENT_PROMPTS_ARCHIVE.md`

---

## Current prompts

## Prompt — Agent A (B29-A) — Fix Drift Permanently: Run Reports + Prompt Archive + Checklist Hygiene

## Model + MAX mode + Cycle
- **Model used:** <model-name> (see REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md)
- **MAX mode:** ON | OFF
- **Cycle:** 2× (Cycle 1 implement, Cycle 2 review + edge cases)

```text
✅ Agent A Prompt (B29-A) — Fix Drift Permanently: Run Reports + Prompt Archive + Checklist Hygiene

Cycle: 2× (Cycle 1 implement, Cycle 2 review + edge cases)

Mission

Make it impossible to run agents without generating durable run history, and make it impossible for PM to accidentally send the same prompts again.

Deliverables (must land in repo)
1) Run-report enforcement (CI-hard requirement)

Update the repo so CI fails if the latest run folder is missing or empty.

Update scripts/verify_rehydration_pack.py (or add a dedicated script) so that in MODE=build:

REHYDRATION_PACK/RUNS/ must contain at least one RUN_* directory.

The latest run must have A/, B/, C/ subfolders.

Each agent folder must contain populated files:

RUN_REPORT.md (new required artifact)

RUN_SUMMARY.md

STRUCTURE_REPORT.md

DOCS_IMPACT_MAP.md

TEST_MATRIX.md

“Populated” rule: at least 25 non-empty lines in RUN_REPORT.md, and at least 10 non-empty lines in each of the other required docs.

Wire this into:

scripts/run_ci_checks.py so it runs on every validate.

CI must go red if reports are missing.

2) Add/upgrade templates so agents can’t “half-report”

In REHYDRATION_PACK/TEMPLATES/:

Add Agent_Run_Report_TEMPLATE.md (high-detail: diffstat, files touched, tests run, PR link, worktree path, blockers, follow-ups).

Update scripts/new_run_folder.py so it creates RUN_REPORT.md in A/B/C folders from that template automatically.

3) Prompt archive enforcement (so dedup actually works)

Right now scripts/verify_agent_prompts_fresh.py expects archived prompts but the repo isn’t consistently archiving them.

Make scripts/new_run_folder.py also create:

REHYDRATION_PACK/RUNS/<RUN_ID>/C/AGENT_PROMPTS_ARCHIVE.md
…and copy in the current REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md content automatically.

Also update REHYDRATION_PACK/RUNS/README.md to make this an explicit requirement.

4) Checklist + task board hygiene (align docs to reality)

Update these to match what’s actually shipped (and clearly label shipped vs roadmap):

docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md

REHYDRATION_PACK/05_TASK_BOARD.md

Also add a small “progress dashboard” section (counts + % complete) and ensure it doesn’t make claims about staging/prod unless verified.

Tests / Proof

Run and paste evidence into your RUN_REPORT:

AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python scripts/run_ci_checks.py

PR requirements

Branch: run/B29_run_report_enforcement_20260110

PR: open + auto-merge (merge commit) + delete branch

Trigger Bugbot with @cursor review
```

## Prompt — Agent B (no tasks assigned)

## Model + MAX mode + Cycle
- **Model used:** <model-name> (see REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md)
- **MAX mode:** ON | OFF
- **Cycle:** 2× (Cycle 1 implement, Cycle 2 review + edge cases)

```text
No tasks assigned in this cycle. Do not make changes.
```

## Prompt — Agent C (no tasks assigned)

## Model + MAX mode + Cycle
- **Model used:** <model-name> (see REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md)
- **MAX mode:** ON | OFF
- **Cycle:** 2× (Cycle 1 implement, Cycle 2 review + edge cases)

```text
No tasks assigned in this cycle. Do not make changes.
```
