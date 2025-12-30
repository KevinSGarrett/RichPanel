# GitHub and Repo Operations Policy (Cursor Agents)

**Doc ID:** POL-GH-001  
**Status:** Canonical  
**Last updated:** 2025-12-29  

This policy defines how Cursor agents (A/B/C) must handle **all Git/GitHub operations** so that:

- **merge conflicts are rare and easy to resolve**
- **main is continuously updated** (no “stuck on branches” problem)
- **CI stays green** (and agents can self-fix when it isn’t)
- **the repo structure and documentation are never accidentally deleted**
- **branch count stays low** (no 50–100 branch explosions)

This policy is designed for your workflow:
- Human does **no manual development**
- ChatGPT is the PM (plans/coordination)
- Cursor agents implement, commit, push, open/merge PRs, clean up branches, fix CI

---

## 0) Non‑negotiables

1) **One source of truth:** `main` is the canonical source of truth.
2) **No run is “done” until main is updated** and CI is green (or explicitly waived by PM).
3) **Never delete protected paths** (docs/packs/policies) unless explicitly approved and recorded.
4) **No uncontrolled branch creation:** branches must follow the naming rules below and be cleaned up.

---

## 1) Default branch strategy (recommended)

### 1.1 Run branch (always)
For every PM cycle/run, use a single run branch:

- `run/<RUN_ID>`

Example:
- `run/RUN_20251229_2210Z`

This branch exists to collect work, reduce risk, and produce a single integration point.

### 1.2 Sequential mode (preferred; lowest conflict)
Use **one branch total** per run:

- All agents work on **the same** `run/<RUN_ID>` branch, one after another (A → B → C).
- Each agent must `git pull --rebase` before starting.
- Each agent commits/pushes only their scoped changes.

When to use: whenever agents might touch overlapping files, shared schemas, or shared docs.

### 1.3 Parallel mode (allowed; still low-branch)
If the PM assigns **disjoint scopes**, parallel work is allowed with **max 3 agent branches**:

- `run/<RUN_ID>-A`
- `run/<RUN_ID>-B`
- `run/<RUN_ID>-C`

Integration rules:
- One agent is assigned **Integrator** (default: Agent A unless PM specifies otherwise).
- Integrator merges A/B/C branches into `run/<RUN_ID>` and resolves conflicts.
- Then Integrator merges `run/<RUN_ID>` → `main`.

**Hard limit:** At most **4** branches per run (run branch + 3 agent branches).

---

## 2) Branch creation rules (anti-branch-explosion)

Agents may only create branches with these prefixes:

- `run/`
- `hotfix/`
- `release/`

Disallowed (unless PM explicitly requests):
- ad-hoc branches like `fix-xyz`, `test`, `tmp`, `wip-*`

### 2.1 Branch budget
- Maintain **< 10 active** remote branches at any time.
- Delete run branches immediately after merging to main.
- The repo must not accumulate old run branches.

A helper check exists:
- `python scripts/branch_budget_check.py`

---

## 3) Avoiding merge conflicts (required)

### 3.1 PM assigns explicit scopes
Every agent prompt must include:
- **Allowed paths** (where the agent may edit)
- **Locked paths** (where the agent must NOT edit)

The PM records these in the run Git plan:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md`

### 3.2 Do not edit shared coordination files in parallel
In parallel mode, agents must not edit:
- `REHYDRATION_PACK/02_CURRENT_STATE.md`
- `REHYDRATION_PACK/05_TASK_BOARD.md`
- `REHYDRATION_PACK/04_DECISIONS_SNAPSHOT.md`

Instead, each agent writes into their own folder:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<A|B|C>/...`

Integrator (or PM) consolidates after.

### 3.3 Rebase discipline
Before starting work:
- `git checkout <branch>`
- `git pull --rebase`

Before pushing:
- ensure local tests pass
- ensure registry files are regenerated (if needed)
- ensure working tree is clean except intended changes

---

## 4) Main branch update rule (prevents “main never updated”)

At the end of every run:

1) Integrator merges `run/<RUN_ID>` into `main`
2) Integrator pushes `main`
3) Integrator records in:
   - `REHYDRATION_PACK/GITHUB_STATE.md`
     - merged commit hash
     - CI status link/id if available
     - branches deleted

**Definition:** A run is not complete if `main` was not updated.

---

## 5) PR vs direct merge (default + fallback)

### 5.1 Default: PR-based merge (preferred)
- Create PR from `run/<RUN_ID>` → `main`
- Merge PR using squash or merge-commit (PM decides; default: **merge commit** to keep run boundaries)
- Delete branch after merge

Agents should use GitHub CLI if available:
- `gh pr create --fill`
- `gh pr merge --merge --delete-branch`

### 5.2 Fallback: direct merge (allowed if PR automation unavailable)
If `gh` is not available or auth is not configured:
- `git checkout main`
- `git pull`
- `git merge --no-ff run/<RUN_ID>`
- `git push origin main`
- delete branches manually via:
  - `git push origin --delete run/<RUN_ID>`

---

## 6) CI / GitHub Actions must be green (agents self-fix)

### 6.1 Local CI-equivalent checks (required before push)
Agents must run:
- `python scripts/run_ci_checks.py`

### 6.2 If Actions are red
The responsible agent (or Integrator if unclear) must:
1) Pull the failing logs (preferred via `gh run view`)
2) Reproduce locally (or explain why not possible)
3) Fix the issue
4) Add a **Fix Report**:
   - `docs/00_Project_Admin/Issue_Log.md` (index entry)
   - `docs/00_Project_Admin/Issues/<ISSUE_ID>.md` (full details)
5) Add test evidence:
   - `docs/08_Testing_Quality/Test_Evidence_Log.md`
   - raw artifacts under `qa/test_evidence/<RUN_ID>/...`
6) Push fix commit(s) until green

---

## 7) Protected paths (anti-accidental deletion)

The following paths are protected:
- `docs/`
- `REHYDRATION_PACK/`
- `PM_REHYDRATION_PACK/`
- `policies/`
- `reference/`
- `.github/`
- `scripts/`
- `config/`
- root files: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`

Agents must never delete/rename items in protected paths unless:
- PM explicitly approves, AND
- the approval is recorded in:
  - `REHYDRATION_PACK/DELETE_APPROVALS.yaml`

Automated guard:
- `python scripts/check_protected_deletes.py`

---

## 8) Branch cleanup (required)
After merging to main:
- delete `run/<RUN_ID>` and any `run/<RUN_ID>-A/B/C` branches
- ensure remote branch list stays small

Record cleanup in:
- `REHYDRATION_PACK/GITHUB_STATE.md`

---

## 9) Related docs
- `docs/08_Engineering/GitHub_Workflow_and_Repo_Standards.md`
- `docs/08_Engineering/Multi_Agent_GitOps_Playbook.md`
- `docs/08_Engineering/CI_and_Actions_Runbook.md`
- `docs/98_Agent_Ops/Living_Documentation_Set.md`

Related:
- `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
