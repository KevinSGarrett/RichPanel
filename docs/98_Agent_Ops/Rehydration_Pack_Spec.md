# Rehydration Pack Spec

Last updated: **2025-12-29** (Wave F03)

This document defines **what must exist**, **how it must be maintained**, and **how validation works** for:

- `REHYDRATION_PACK/` (the *implementation-cycle* operational pack)
- the two operational modes:
  - `foundation` — building the repo OS (structure + docs)
  - `build` — executing Cursor agent run sets (implementation work)

This spec is written for **AI workers** (Cursor agents) and the **ChatGPT PM**.

---

## Purpose

The rehydration pack exists so the ChatGPT PM can:

- re-hydrate context in **minutes, not hours**
- avoid token blowups by reading only small, curated files
- trace decisions and progress without re-reading the entire repo
- (in build mode) audit what each agent did per run set

The rehydration pack is **not** a duplicate of the entire docs library. It is the **control panel** that points to canonical docs.

Canonical docs live under:
- `docs/INDEX.md` (curated navigation)
- `docs/REGISTRY.md` (complete listing)
- `docs/_generated/*` (machine registries)

---

## Operating modes

The active mode is stored in:
- `REHYDRATION_PACK/MODE.yaml`

### Mode: foundation
Use when you are still building:
- file/folder structure
- documentation library
- indexing/chunking standards
- validation automation
- policies / guardrails

**In foundation mode:**
- Cursor run artifacts are **not required**.
- `REHYDRATION_PACK/RUNS/` may be missing or empty.
- The pack should still contain **build-mode templates**, but they are not executed.

### Mode: build
Use when you begin implementation with Cursor agents.

**In build mode:**
- each run set must produce a run folder under `REHYDRATION_PACK/RUNS/`
- per-agent artifacts are required and must follow templates
- validation should be strict before handing control back to the PM

---


## PM prompt helpers

To make the ChatGPT PM loop deterministic, the pack includes two copy/paste prompts:

- `REHYDRATION_PACK/PM_INITIAL_PROMPT.md` — paste once per new PM chat
- `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md` — paste at the start of each cycle

These prompts are optional helpers, but they should be treated as the default PM workflow.

---
## Required pack contents

The authoritative list lives in:
- `REHYDRATION_PACK/MANIFEST.yaml` (version 2, mode-aware)

**Do not add “secret required files” that are not listed in the manifest.**  
If it matters, it must be listed.

### File size guidelines
To prevent token blowups, keep these guidelines:

- `00_START_HERE.md`: **< 300 lines**
- `02_CURRENT_STATE.md`: **< 400 lines**
- `05_TASK_BOARD.md`: **< 400 lines**
- `04_DECISIONS_SNAPSHOT.md`: **< 250 lines**

If a topic needs more space, create or update a canonical doc under `docs/` and link to it.

---

## MANIFEST.yaml requirements

`MANIFEST.yaml` is the machine-checked contract.

### Version
- Current: `version: 2`

### Path entry fields
Each entry in `paths:` must include:

- `path`: relative to `REHYDRATION_PACK/`  
  - use trailing `/` for directories
- `kind`: `file` or `dir`
- `when`:
  - `common` — required in all modes
  - `foundation` — required only when `mode: foundation`
  - `build` — required only when `mode: build`
- `required`: `true` or `false`
- `role`: short human-readable description

### Build-mode run artifact spec
The `run_artifacts:` section defines:

- `run_id_regex` (default: `^RUN_\d{8}_\d{4}Z$`)
- `agent_ids` (default: `['A','B','C']`)
- `required_files_per_agent` (run summary, structure report, docs impact, test matrix)
- `optional_files_per_agent` (e.g. fix report)

---

## Build mode run folder protocol

**Only applies in build mode.**

Each Cursor run set produces:

```
REHYDRATION_PACK/RUNS/<RUN_ID>/
  A/
  B/
  C/
```

Where `<RUN_ID>` matches the manifest regex, typically:

`RUN_<YYYYMMDD>_<HHMMZ>` (UTC)

Each agent folder must include:

- `RUN_SUMMARY.md`
- `STRUCTURE_REPORT.md`
- `DOCS_IMPACT_MAP.md`
- `TEST_MATRIX.md`
- `FIX_REPORT.md` *(optional; only if fixes were needed)*

Templates live in:
- `REHYDRATION_PACK/_TEMPLATES/`

---

## Update responsibilities

### In foundation mode (this phase)
After every wave that changes structure or docs:

- update `REHYDRATION_PACK/MODE.yaml` (`current_wave`)
- update `REHYDRATION_PACK/LAST_REHYDRATED.md`
- update `REHYDRATION_PACK/02_CURRENT_STATE.md` (high-level truth)
- update `REHYDRATION_PACK/04_DECISIONS_SNAPSHOT.md` (only if decisions changed)
- update `REHYDRATION_PACK/05_TASK_BOARD.md` (next work)
- update `docs/INDEX.md` when new canonical docs are added
- run `python scripts/regen_doc_registry.py` and commit outputs

### In build mode (later)
After each full run set:

- create run artifacts under: `REHYDRATION_PACK/RUNS/<RUN_ID>/{A,B,C}/`
  - `RUN_SUMMARY.md`
  - `STRUCTURE_REPORT.md`
  - `DOCS_IMPACT_MAP.md`
  - `TEST_EVIDENCE.md` (if tests were run)
  - `NOTES.md` (optional)
- update `REHYDRATION_PACK/02_CURRENT_STATE.md` with progress + issues
- update `REHYDRATION_PACK/05_TASK_BOARD.md`
- update `docs/INDEX.md` if new canonical docs were created
- regenerate doc registries

---

## Validation

Run these from repo root:

```bash
python scripts/verify_rehydration_pack.py
python scripts/regen_doc_registry.py
python scripts/verify_plan_sync.py
```

Notes:
- `verify_rehydration_pack.py` is **mode-aware** (reads `MODE.yaml`)
- In build mode, run folder validation is strict by default.
- Use `--allow-partial` only for *in-progress* run sets.

---

## Drift prevention rules

- **One source of truth:** canonical decisions go in `docs/00_Project_Admin/Decision_Log.md`.
- **No silent structure changes:** update `docs/CODEMAP.md` + regenerate registries.
- **Index-first:** anything important must be linked from `docs/INDEX.md` or the rehydration pack.
- **No giant pack files:** push detail into `docs/` and link to it.
