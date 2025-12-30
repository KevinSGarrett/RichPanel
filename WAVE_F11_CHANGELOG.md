# Wave F11 Changelog — Multi-agent GitHub Ops hardening

Date: 2025-12-29  
Mode: foundation

## Goals
- Prevent merge conflicts in multi-agent development
- Prevent branch explosion (50–100 branches)
- Ensure main is continuously updated
- Ensure agents can self-fix CI red status
- Ensure no critical docs/policies/packs are accidentally deleted

## Key changes
- Updated policy:
  - `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
- Added playbooks:
  - `docs/08_Engineering/Multi_Agent_GitOps_Playbook.md`
  - `docs/08_Engineering/CI_and_Actions_Runbook.md`
  - `docs/08_Engineering/Protected_Paths_and_Safe_Deletion_Rules.md`
- Added CI-equivalent script:
  - `scripts/run_ci_checks.py`
- Added Git safety scripts:
  - `scripts/check_protected_deletes.py`
  - `scripts/branch_budget_check.py`
- Run scaffolding now includes Git plan:
  - `REHYDRATION_PACK/_TEMPLATES/Git_Run_Plan_TEMPLATE.md`
  - `scripts/new_run_folder.py` copies it into each run root as `GIT_RUN_PLAN.md`
- Rehydration pack additions:
  - `REHYDRATION_PACK/GITHUB_STATE.md`
  - `REHYDRATION_PACK/DELETE_APPROVALS.yaml`
  - manifest updated to require these
- GitHub Actions:
  - `.github/workflows/ci.yml` runs `python scripts/run_ci_checks.py --ci`

## Validation
- `python scripts/verify_rehydration_pack.py` ✅
- `python scripts/verify_doc_hygiene.py` ✅
- `python scripts/verify_plan_sync.py` ✅
