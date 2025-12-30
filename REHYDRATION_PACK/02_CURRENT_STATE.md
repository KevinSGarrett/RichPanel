# Current State (Truth)

**As of:** 2025-12-30 (Wave B00)  
**Mode:** build (see `REHYDRATION_PACK/MODE.yaml`)  
**Stage:** build kickoff — Cursor agents take over implementation + GitOps

---

## What exists now

### GitHub + CI are live
- Repo is hosted on GitHub (`KevinSGarrett/RichPanel`).
- CI workflow runs repo validations (`python scripts/run_ci_checks.py --ci`).
- `main` is protected with required status check **`validate`**.

### Deterministic regen system
- `regen_doc_registry.py` uses a canonical POSIX-path sort key.
- `regen_reference_registry.py` uses canonical sorting and normalizes newline handling for stable `size_bytes`.
- `regen_plan_checklist.py` emits a deterministic banner so markdown outputs stop thrashing.

### Canonical plan + doc library
- Canonical documentation library under `docs/`.
- Curated navigation:
  - `docs/INDEX.md`
  - `docs/CODEMAP.md`
  - `docs/ROADMAP.md`

### Change Requests
- CR-001 (No tracking / Delivery estimates) is scoped and integrated into the plan docs.

### Operational packs
- Rehydration pack:
  - `REHYDRATION_PACK/` (this folder)
  - validated by `python scripts/verify_rehydration_pack.py`
- PM meta pack:
  - `PM_REHYDRATION_PACK/`

---

## What does NOT exist yet (still expected)
- Full production implementation (automation runners, integrations, end-to-end tests).
- Non-empty run history under `REHYDRATION_PACK/RUNS/` (will start in build mode).

---

## Next focus
- Execute **WAVE_B00** assignments in `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`.
- Begin Sprint 0 preflight + Sprint 1 scaffolding per:
  - `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md`
  - `docs/12_Cursor_Agent_Work_Packages/01_Sprint_0_Preflight/`

---

## GitHub ops
- Branch protection + merge settings are documented in:
  - `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
