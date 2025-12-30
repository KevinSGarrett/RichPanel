# Wave F12 — GitHub Defaults Locked + Branch Protection + Protected Delete Guard

Date: 2025-12-29

## What changed
- Added canonical GitHub settings guide:
  - `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
- Fixed protected delete guard so it no longer emits confusing skip warnings and it works:
  - pre-commit (staged + working tree diffs)
  - CI (commit-range diffs)
- Updated:
  - `docs/INDEX.md` (added link)
  - GitHub workflow docs/policies to reference the settings guide
  - `scripts/run_ci_checks.py` to pass `--ci` to the protected delete check when running in CI mode
  - `scripts/verify_plan_sync.py` to require the new canonical settings doc

## Validation
Run:
- `python scripts/run_ci_checks.py`
Expected:
- `[OK] CI-equivalent checks passed.`
- No confusing skip warnings from protected delete checks.
