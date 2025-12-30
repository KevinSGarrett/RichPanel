# Foundation Status (Snapshot)

Last updated: 2025-12-29 — Wave F11

This is a **token-efficient snapshot** of where we are in the documentation OS build.

Mode:
- `foundation` (see `REHYDRATION_PACK/MODE.yaml`)

## Foundation completion criteria
Foundation (documentation OS) is considered complete when these pass:
- `python scripts/verify_rehydration_pack.py`
- `python scripts/verify_plan_sync.py`
- `python scripts/verify_doc_hygiene.py`

Definition of Done (canonical):
- `docs/00_Project_Admin/Definition_of_Done__Foundation.md`

## What is already in place
- REHYDRATION_PACK is manifest-driven and mode-aware (foundation vs build).
- Docs indexing/registries exist (`docs/_generated/*`) and regenerate deterministically.
- Reference registry exists (`reference/_generated/*`) and regenerates deterministically.
- Plan checklist extraction works (`docs/00_Project_Admin/To_Do/_generated/*`).
- PM prompt helpers exist:
  - `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
  - `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`
- Build-mode run archive structure exists:
  - `REHYDRATION_PACK/RUNS/` (+ `scripts/new_run_folder.py`)

## What remains before build mode
See the canonical checklist:
- `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`

High-level remaining steps:
- [ ] Build-mode activation checklist complete
- [ ] Switch `REHYDRATION_PACK/MODE.yaml` to `mode: build`
- [ ] Create first run folder: `python scripts/new_run_folder.py --now`
- [ ] Populate `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`
- [ ] First run set executed and required run artifacts filled in


## GitHub ops readiness (build-mode prerequisite)
- ✅ GitHub operations policy is explicit (`POL-GH-001`)
- ✅ CI-equivalent script exists (`scripts/run_ci_checks.py`)
- ✅ Protected delete guard exists (`scripts/check_protected_deletes.py` + approvals file)
- ✅ Branch budget helper exists (`scripts/branch_budget_check.py`)
- ✅ Run scaffolding includes `GIT_RUN_PLAN.md`
- ✅ Pack includes `GITHUB_STATE.md` for PM visibility
