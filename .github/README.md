# GitHub Templates

This folder contains GitHub-facing templates (issues/PRs).

These templates are designed for an AI-managed repo:
- consistent context
- traceable changes (RUN_ID / Task IDs)
- explicit test evidence expectations

If you do not use GitHub issues/PRs, you can ignore this folder.
Canonical internal tracking still lives in:
- `docs/00_Project_Admin/Issue_Log.md`
- `docs/00_Project_Admin/Issues/`


## Workflows
- `CI` workflow runs `python scripts/run_ci_checks.py --ci` on PRs and main pushes.
