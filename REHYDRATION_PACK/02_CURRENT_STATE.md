# Current State (Truth)

**As of:** 2025-12-29 (Wave F13)  
**Mode:** foundation (see `REHYDRATION_PACK/MODE.yaml`)  
**Stage:** building the repo + documentation OS for AI-managed implementation

---

## What exists now

### Recent changes (Wave F13)
- CR-001 scoped: no-tracking delivery estimate automation for order-status tickets (SLA-based ETA + controlled auto-close whitelist)


### Canonical plan library
- Canonical documentation library under `docs/` (plan + specs + living docs)
- Curated navigation:
  - `docs/INDEX.md`
  - `docs/CODEMAP.md`
  - `docs/ROADMAP.md`

### Indexes / registries (generated)
- Docs registry + heading index:
  - `docs/REGISTRY.md`
  - `docs/_generated/doc_registry.json`
  - `docs/_generated/heading_index.json`
- Wave naming + mapping:
  - `docs/00_Project_Admin/Wave_Naming_and_Mapping.md`
- Foundation completion definition:
  - `docs/00_Project_Admin/Definition_of_Done__Foundation.md`

- Reference registry:
  - `reference/_generated/reference_registry.json`

Doc hygiene:
- `python scripts/verify_doc_hygiene.py` passes cleanly (no ambiguous placeholders in INDEX-linked docs)

### Operational packs
- PM prompt helpers:
  - `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
  - `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`

- Rehydration pack:
  - `REHYDRATION_PACK/` (this folder)
  - validated by `python scripts/verify_rehydration_pack.py`
- PM meta pack:
  - `PM_REHYDRATION_PACK/` (keeps this window aligned)

### Living docs set
Defined in:
- `docs/98_Agent_Ops/Living_Documentation_Set.md`

Pointer map:
- `REHYDRATION_PACK/CORE_LIVING_DOCS.md`

### Plan → checklist extraction
Generated compiled view exists:
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`
- `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`

---

## What does NOT exist yet (by design)

- The real implementation code is not built yet.
- Cursor agent run history under `REHYDRATION_PACK/RUNS/` may be empty in foundation mode.
- CI/CD pipelines may not be configured yet.

---

## Next focus

Build-mode activation:
- `REHYDRATION_PACK/FOUNDATION_STATUS.md`
- `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- `REHYDRATION_PACK/05_TASK_BOARD.md`



## GitHub ops
- GitHub guardrails for multi-agent work are now in place (POL-GH-001 + run git plan template + protected delete guard + CI entrypoint).
