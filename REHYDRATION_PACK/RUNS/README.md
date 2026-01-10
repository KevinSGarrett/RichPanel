# RUNS — Build-Mode Run Archive

This folder is used in **build mode** only.

Each build cycle is a **run set** identified by:

`RUN_<YYYYMMDD>_<HHMMZ>` (UTC)

Example:
- `RUN_20251229_2315Z/`

Structure (required):

```
REHYDRATION_PACK/RUNS/<RUN_ID>/
  A/
    RUN_REPORT.md
    RUN_SUMMARY.md
    STRUCTURE_REPORT.md
    DOCS_IMPACT_MAP.md
    TEST_MATRIX.md
  B/
    RUN_REPORT.md
    RUN_SUMMARY.md
    STRUCTURE_REPORT.md
    DOCS_IMPACT_MAP.md
    TEST_MATRIX.md
  C/
    AGENT_PROMPTS_ARCHIVE.md
    RUN_REPORT.md
    RUN_SUMMARY.md
    STRUCTURE_REPORT.md
    DOCS_IMPACT_MAP.md
    TEST_MATRIX.md
```

Optional per agent:
- `FIX_REPORT.md` (only when something broke and was repaired)

## Create a new run folder
Use:

```bash
python scripts/new_run_folder.py --now
```

or provide a specific run id:

```bash
python scripts/new_run_folder.py RUN_20251229_2315Z
```

Notes:
- `new_run_folder.py` copies templates into `A/`, `B/`, `C/` including `RUN_REPORT.md`.
- `new_run_folder.py` also snapshots the current `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` into `C/AGENT_PROMPTS_ARCHIVE.md` to support prompt dedup.

## Validation
In build mode, run artifacts are enforced by:

```bash
python scripts/verify_rehydration_pack.py --strict
```

Latest-run reporting invariants (CI-hard):
- `REHYDRATION_PACK/RUNS/` must contain at least one `RUN_*` folder.
- The **latest** `RUN_*` folder must have `A/`, `B/`, `C/`.
- Each agent folder must include populated files:
  - `RUN_REPORT.md` (>= 25 non-empty lines)
  - `RUN_SUMMARY.md`, `STRUCTURE_REPORT.md`, `DOCS_IMPACT_MAP.md`, `TEST_MATRIX.md` (>= 10 non-empty lines each)

## Prompt set fingerprint (anti-duplicate convention)

To prevent “same prompts again” loops, we treat the active prompt set as a versioned artifact.

- **What it is**: a stable SHA-256 fingerprint of the *semantic prompt bodies* in `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` (after normalization that strips run IDs, timestamps, and other non-semantic headers).
- **Where it comes from**: `python scripts/verify_agent_prompts_fresh.py` (also printed during `python scripts/run_ci_checks.py`).
- **How to use it**:
  - When you update prompts, run the script and copy:
    - `[INFO] Prompt set fingerprint: <sha256>`
  - Paste that fingerprint into your agent’s `RUN_SUMMARY.md` under “Merge state” (see `REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md`).
  - Include it in the PR description when the PR changes prompts (recommended).