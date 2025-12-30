# Definition of Done — Build Mode Readiness

Last updated: 2025-12-29  
Status: Canonical

This doc defines when the repo’s **structure + documentation OS** is ready to start implementation using Cursor agents (Build Mode).

Build Mode starts when:
- `REHYDRATION_PACK/MODE.yaml` is set to `mode: build`

---

## Required (must be true)
- [ ] `python scripts/verify_rehydration_pack.py` passes
- [ ] `python scripts/verify_plan_sync.py` passes
- [ ] `python scripts/verify_doc_hygiene.py` passes
- [ ] PM prompts exist:
  - `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
  - `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`
- [ ] Run scaffolding exists:
  - `python scripts/new_run_folder.py --now` creates A/B/C run folders with templates
  - includes `GIT_RUN_PLAN.md`
- [ ] GitHub ops policy exists and is explicit:
  - `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
- [ ] CI-equivalent entrypoint exists:
  - `python scripts/run_ci_checks.py`
- [ ] Protected delete guard exists:
  - `python scripts/check_protected_deletes.py`
  - approvals file exists: `REHYDRATION_PACK/DELETE_APPROVALS.yaml`

---

## Recommended (strongly suggested)
- [ ] GitHub Actions workflow runs validations:
  - `.github/workflows/ci.yml`
- [ ] GitHub settings align to agent autonomy:
  - agents can create/merge PRs (recommended via GitHub CLI)
  - branches auto-delete on merge
  - required status checks configured on `main`

---

## When this is satisfied
You can safely start **B00** (the first build run) with low drift and low GitHub risk.
