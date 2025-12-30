# Canonical vs Legacy Documentation Paths

Last verified: 2025-12-29 — Wave F06 (canonical paths clarified; legacy redirects standardized).

This repo contains a large documentation library and a rehydration pack.
To prevent AI drift, we explicitly define what is **canonical** vs **legacy**.

---

## What “canonical” means

A canonical doc/path is a **source of truth** that AI agents should:
- read first
- update when they make relevant changes
- reference in prompts and run summaries

Legacy docs may be preserved for historical context but should not be treated as source-of-truth without confirmation.

---

## Primary entrypoints (canonical)

### Rehydration pack (operational loop)
- `REHYDRATION_PACK/00_START_HERE.md` — read order + what to update
- `REHYDRATION_PACK/MODE.yaml` — `foundation` vs `build`
- `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` — authoritative wave plan
- `REHYDRATION_PACK/CORE_LIVING_DOCS.md` — pointer map to “always-update” docs

### Curated docs navigation
- `docs/INDEX.md` — curated navigation
- `docs/CODEMAP.md` — repo structure map
- `docs/REGISTRY.md` — complete docs list (generated)

### Living docs (always updated during build)
Canonical list + update triggers:
- `docs/98_Agent_Ops/Living_Documentation_Set.md`

---

## Canonical “always-update” files (repo root)

- `CHANGELOG.md` — canonical chronological change log
- `config/.env.example` — canonical non-secret env template
- `scripts/` — canonical automation/verification scripts

---

## Machine registries (canonical)

Generated (do not hand-edit):
- `docs/_generated/doc_registry.json`
- `docs/_generated/doc_outline.json`
- `docs/_generated/heading_index.json`
- `reference/_generated/reference_registry.json`

Regeneration:
- `python scripts/regen_doc_registry.py`
- `python scripts/regen_reference_registry.py`

---

## Legacy / redirect paths

Some folders exist only to preserve older links. They contain **stubs** that point to canonical locations.

Legacy redirect list:
- `docs/00_Project_Admin/Legacy_Folder_Redirects.md`

Current legacy redirects include:
- `docs/06_Data_Privacy_Observability/` → `docs/06_Security_Privacy_Compliance/` and `docs/08_Observability_Analytics/`
- `docs/10_Governance_Continuous_Improvement/` → `docs/11_Governance_Continuous_Improvement/`
- `docs/11_Cursor_Agent_Work_Packages/` → `docs/12_Cursor_Agent_Work_Packages/`

---

## Rules for AI workers (anti-drift)

1) **Prefer what’s linked from `docs/INDEX.md`.**  
   If something is not in the INDEX, treat it as supplemental/legacy unless proven otherwise.

2) **Treat redirect folders as read-only.**  
   If you land in a redirect folder, follow the pointer and edit the canonical target instead.

3) **Update the “living docs” when you change things.**  
   The system is only explainable if living docs stay current.

4) **Regenerate registries when docs move.**  
   Run:
   - `python scripts/regen_doc_registry.py`
   - `python scripts/verify_plan_sync.py`

