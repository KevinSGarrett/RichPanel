# Rehydration Pack — Start Here

Last verified: 2026-01-03 — Dev + staging deployed; smoke tests green; prod gated.

This folder is the **token-efficient control panel** for the ChatGPT browser-window project manager.

It is designed for AI-first work:

**New in Wave F13:** CR-001 scoped (no-tracking delivery estimate automation for order-status tickets).
- index-first navigation (no hunting)
- small, stable files (avoid token blowups)
- explicit pointers to canonical docs (`docs/INDEX.md`)
- minimal “current state” snapshots + links to deeper sources

---



## PM prompt helpers
- One-time setup: `PM_INITIAL_PROMPT.md`
- Every cycle: `PM_REHYDRATION_PROMPT.md`

## What to attach to the PM (this chat)
To avoid drift and reduce token usage, always provide:
- the repo zip (includes this `REHYDRATION_PACK/`)
- a standalone `REHYDRATION_PACK.zip` (for quick access in the ChatGPT window)

Optional (recommended for long multi-wave work):
- `PM_REHYDRATION_PACK.zip` (meta pack that keeps this chat aligned)


---

## Mode awareness
The active mode is stored in:
- `REHYDRATION_PACK/MODE.yaml`

Modes:
- `foundation` — build the repo OS (structure/docs/indexes/policies); no Cursor RUN artifacts required
- `build` — run Cursor agents and store per-run artifacts under `REHYDRATION_PACK/RUNS/`

**Note**
- If your goal is only **file/folder structure + documentation**, you can stop after Phase **F**.
- Do **not** switch to `build` mode until you are ready to begin implementation.

---

## Read order (build mode — current)
1. `MODE.yaml` — confirm we are in **build** mode
2. `LAST_REHYDRATED.md` — last snapshot refresh / wave applied
3. `02_CURRENT_STATE.md` — snapshot of “what is true right now” (**includes completion %**)
4. `05_TASK_BOARD.md` — what to do next (source of truth)
5. `03_ACTIVE_WORKSTREAMS.md` — active focus areas + blockers
6. `04_DECISIONS_SNAPSHOT.md` — key decisions
7. `GITHUB_STATE.md` — GitHub/CI merge constraints + how to verify
8. `CORE_LIVING_DOCS.md` — pointers to the “always-update” documentation set
9. `PM_GUARDRAILS.md` — guardrails for PM behavior
10. `POLICIES_SUMMARY.md` — condensed agent policies
11. `OPEN_QUESTIONS.md` — unresolved decisions/questions

Canonical deep navigation:
- `docs/INDEX.md`
- `docs/CODEMAP.md`
- `docs/REGISTRY.md`

---

## Build mode
Implementation is active. Cursor agents should store per-run artifacts under `REHYDRATION_PACK/RUNS/`.

1) Complete `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`  
2) Switch `REHYDRATION_PACK/MODE.yaml` to:
   - `mode: build`
3) Create a new run skeleton:
   ```bash
   python scripts/new_run_folder.py --now
   ```

### Windows note: PowerShell 5.x does **not** support `&&`
If you see examples that chain commands with `&&` (common in bash/zsh), they will fail in **Windows PowerShell 5.x**.

Use **separate lines** or `;` instead:
```powershell
python scripts/new_run_folder.py --now
python scripts/run_ci_checks.py
```

### What must exist for each run
- `REHYDRATION_PACK/RUNS/<RUN_ID>/RUN_META.md`
- `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md` (**required**; prevents merge conflicts + branch explosion)
- per-agent folders:
  - `REHYDRATION_PACK/RUNS/<RUN_ID>/A/`
  - `REHYDRATION_PACK/RUNS/<RUN_ID>/B/`
  - `REHYDRATION_PACK/RUNS/<RUN_ID>/C/`

Required per-agent files are enforced by:
- `REHYDRATION_PACK/MANIFEST.yaml`
- `python scripts/verify_rehydration_pack.py --strict`

### Git safety files (always present)
- `REHYDRATION_PACK/GITHUB_STATE.md` — snapshot of branches/PRs/CI and last main update
- `REHYDRATION_PACK/DELETE_APPROVALS.yaml` — explicit approvals for any protected deletes/renames

### CI expectations
Agents must run before pushing:
```bash
python scripts/run_ci_checks.py
```
- This run now enforces that `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` differs from
  the latest `RUN_*/C/AGENT_PROMPTS_ARCHIVE*.md` unless you add `Prompt-Repeat-Override: true`
  to confirm intentional reuse.

### “Extensions are not CLI” (VS Code/Cursor)
Do not rely on editor extensions as enforcement mechanisms.

- **Extensions can’t be triggered from CLI/CI** in a dependable way.
- **Enforcement is CI + scripts**: treat `python scripts/run_ci_checks.py` and GitHub Actions as the source of truth.
- **GitHub-side automation (e.g., review bots)** is triggered via PR comments or Actions, not a local extension button.

Policy for Git/GitHub operations:
- `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`

