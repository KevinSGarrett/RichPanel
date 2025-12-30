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
    RUN_SUMMARY.md
    STRUCTURE_REPORT.md
    DOCS_IMPACT_MAP.md
    TEST_MATRIX.md
  B/
    RUN_SUMMARY.md
    STRUCTURE_REPORT.md
    DOCS_IMPACT_MAP.md
    TEST_MATRIX.md
  C/
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

## Validation
In build mode, run artifacts are enforced by:

```bash
python scripts/verify_rehydration_pack.py --strict
```
