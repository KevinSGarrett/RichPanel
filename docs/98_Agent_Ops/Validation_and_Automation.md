# Validation and Automation

Last updated: **2025-12-29** (Wave F03)

This document explains the **lightweight automation** that keeps the repo usable for AI workers:

- rehydration pack invariants
- docs indexes and registries
- link and drift sanity checks

All scripts live under `scripts/` and are designed to be:
- **standard library only**
- runnable locally and in CI
- safe in both foundation and build modes

---

## Recommended command set

Run from repo root:

```bash
python scripts/verify_rehydration_pack.py
python scripts/regen_doc_registry.py
python scripts/verify_plan_sync.py
```

---

## `verify_rehydration_pack.py`

**What it does**
- Reads `REHYDRATION_PACK/MODE.yaml` to determine the active mode.
- Reads `REHYDRATION_PACK/MANIFEST.yaml` to determine what must exist.
- Enforces:
  - required files/dirs for the active mode
  - build-mode run artifact structure when `mode: build`

**Important flags**
- `--strict`  
  Treat warnings as failures.
- `--allow-partial` *(build mode only)*  
  Allow missing agent folders/files as warnings (use only while a run set is in progress).

---

## `regen_doc_registry.py`

Generates:
- `docs/REGISTRY.md` (human-readable complete listing)
- `docs/_generated/doc_registry.json` (machine-readable registry)
- `docs/_generated/doc_registry.compact.json` (smaller version)
- `docs/_generated/doc_outline.json` (heading outlines per doc)
- `docs/_generated/heading_index.json` (heading → doc references)

This enables **index-first retrieval** for AI workers without grepping the whole repo.

---

## `verify_plan_sync.py`

Validates:
- required docs navigation files exist
- generated index JSON files exist and parse
- `docs/INDEX.md` relative links resolve
- the doc registry matches the discovered `docs/**/*.md` files
- heading index points at valid doc paths

---

## When to run validation

### Foundation mode
Run validation after every “structure/docs wave” (including Wave F03 and beyond).

### Build mode
Run validation after each full Cursor run set, **before** zipping and uploading to the PM chat window.

---

## Troubleshooting

If validation fails:

1. Read the failing script output.
2. Update the missing file(s) or regenerate registries.
3. Re-run:
   ```bash
   python scripts/regen_doc_registry.py
   python scripts/verify_plan_sync.py
   python scripts/verify_rehydration_pack.py
   ```
