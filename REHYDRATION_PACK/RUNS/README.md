# RUNS - Build-Mode Run Archive

This folder is used in **build mode** only.

Each build cycle is a **run set** identified by:

`RUN_<YYYYMMDD>_<HHMMZ>` (UTC)

Example:
- `RUN_20251229_2315Z/`

## Structure (required)

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
    RUN_REPORT.md
    RUN_SUMMARY.md
    STRUCTURE_REPORT.md
    DOCS_IMPACT_MAP.md
    TEST_MATRIX.md
    AGENT_PROMPTS_ARCHIVE.md
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

## Validation
In build mode, run artifacts are enforced by:

```bash
python scripts/verify_rehydration_pack.py --strict
```

### Latest run report enforcement (CI-hard requirement)
In **build mode**, CI fails if the **latest** run folder is missing or under-reported.

- **RUNS must contain at least one** `RUN_*` directory.
- The **latest** run must contain `A/`, `B/`, `C/`.
- Each agent folder must contain populated:
  - `RUN_REPORT.md` (>= 25 non-empty lines)
  - `RUN_SUMMARY.md` (>= 10 non-empty lines)
  - `STRUCTURE_REPORT.md` (>= 10 non-empty lines)
  - `DOCS_IMPACT_MAP.md` (>= 10 non-empty lines)
  - `TEST_MATRIX.md` (>= 10 non-empty lines)
- `C/AGENT_PROMPTS_ARCHIVE.md` is created automatically by `scripts/new_run_folder.py` by copying `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`.

## Prompt set fingerprint (anti-duplicate convention)

To prevent "same prompts again" loops, we treat the active prompt set as a versioned artifact.

- **What it is**: a stable SHA-256 fingerprint of the *semantic prompt bodies* in `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` (after normalization that strips run IDs, timestamps, and other non-semantic headers).
- **Where it comes from**: `python scripts/verify_agent_prompts_fresh.py` (also printed during `python scripts/run_ci_checks.py`).
- **How to use it**:
  - When you update prompts, run the script and copy:
    - `[INFO] Prompt set fingerprint: <sha256>`
  - Paste that fingerprint into your agent's `RUN_SUMMARY.md`.
  - Include it in the PR description when the PR changes prompts (recommended).
