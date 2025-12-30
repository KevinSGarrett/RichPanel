# Wave F10 Changelog

Date: 2025-12-29  
Mode: foundation

## Summary
Build-mode readiness hardening without implementing product code:
- deterministic PM prompts
- run folder scaffolding
- GitHub/repo ops policy
- cleaned templates for unambiguous placeholders

## Changes
- Added PM prompt helpers:
  - `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
  - `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`
- Added build-mode run scaffolding:
  - `scripts/new_run_folder.py`
  - `REHYDRATION_PACK/RUNS/README.md`
- Hardened build-mode templates (removed ambiguous placeholder punctuation):
  - `REHYDRATION_PACK/_TEMPLATES/*`
  - `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`
- Added GitHub/repo ops governance:
  - `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
  - `docs/08_Engineering/GitHub_Workflow_and_Repo_Standards.md`
  - `.github/` issue + PR templates
- Updated docs navigation:
  - `docs/INDEX.md` now includes an Engineering/Repo Workflow section and links to Policies index
- Updated rehydration pack schedule and status snapshots for Wave F10.

## Validation
- `python scripts/verify_rehydration_pack.py` → OK
- `python scripts/verify_doc_hygiene.py` → OK
- `python scripts/verify_plan_sync.py` → OK
