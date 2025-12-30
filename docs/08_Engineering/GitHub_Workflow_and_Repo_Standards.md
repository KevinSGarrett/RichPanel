# GitHub Workflow and Repo Standards

Last updated: 2025-12-29  
Status: Canonical

This document defines the practical, day-to-day repo workflow for this project.

For the strict rules, see:
- `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`

---

## 1) Primary goals
- Keep `main` continuously updated (avoid “stale main”)
- Keep CI green (agents fix failures)
- Keep branch count low (avoid branch explosion)
- Avoid merge conflicts by using clear scopes and disciplined integration

---

## 2) Branch naming rules
Allowed prefixes:
- `run/<RUN_ID>`
- `run/<RUN_ID>-A` / `-B` / `-C` (parallel mode only)
- `hotfix/<RUN_ID>`
- `release/<VERSION>`

Disallowed without PM instruction:
- `wip-*`, `tmp-*`, `test-*`, arbitrary branch names

---

## 3) Run structure: sequential vs parallel
Default: **sequential** using a single `run/<RUN_ID>` branch.

Parallel mode is allowed only when:
- PM assigns disjoint file scopes per agent
- Integrator is assigned
- branch cleanup is performed after merge

Details:
- `docs/08_Engineering/Multi_Agent_GitOps_Playbook.md`

---

## 4) Commit message standard
Every commit must include the RUN_ID.

Recommended formats:
- `RUN:<RUN_ID> A <summary>`
- `RUN:<RUN_ID> B <summary>`
- `RUN:<RUN_ID> fix CI: <summary>`
- `RUN:<RUN_ID> docs: <summary>`

---

## 5) Required checks before pushing
Run:
```bash
python scripts/run_ci_checks.py
```

If you change docs structure or reference structure, regenerate registries and commit the output:
```bash
python scripts/regen_doc_registry.py
python scripts/regen_reference_registry.py
python scripts/regen_plan_checklist.py
```

---

## 6) Merging to main
Preferred: PR merge using GitHub CLI (if configured):
- create PR `run/<RUN_ID>` → `main`
- merge with merge commit (default) to preserve run boundary
- delete branches after merge

Fallback: direct `git merge` into `main` is allowed if PR automation is unavailable.

---

## 7) Branch cleanup (mandatory)
After merging to main:
- delete `run/<RUN_ID>` and any agent branches
- ensure branch budget stays low

Helper:
```bash
python scripts/branch_budget_check.py
```

---

## 8) Protected paths (never delete casually)

Also configure GitHub settings:
- `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
See:
- `docs/08_Engineering/Protected_Paths_and_Safe_Deletion_Rules.md`
- guard script: `python scripts/check_protected_deletes.py`
