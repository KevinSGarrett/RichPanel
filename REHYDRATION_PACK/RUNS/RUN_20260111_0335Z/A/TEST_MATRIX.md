# Test Matrix

**Run ID:** `RUN_20260111_0335Z`  
**Agent:** A  
**Date:** 2026-01-11

## Test coverage

| Test ID | Command | Result | Evidence |
|---------|---------|--------|----------|
| T1 | `python scripts/run_ci_checks.py` (before artifact population) | FAIL (expected) | Detected placeholders in RUN_20260111_0335Z artifacts with line numbers |
| T2 | `python scripts/run_ci_checks.py` (after artifact population) | PASS | All checks passed including placeholder enforcement |
| T3 | Verify templates exempt from enforcement | PASS | _TEMPLATES/ files not flagged by placeholder check |

## Manual verification steps
1. Created new run folder with `python scripts/new_run_folder.py --now`
2. Ran CI checks before populating artifacts — confirmed placeholder detection works
3. Populated artifacts with complete documentation (no placeholders)
4. Re-ran CI checks — confirmed pass

## Edge cases tested
- Latest run enforcement (not historical runs) — Working as designed
- Template exemption — Templates correctly excluded from placeholder check
- Multiple placeholder types — All defined patterns detected correctly

## Test gaps
None identified for this scope (placeholder enforcement is straightforward pattern matching)

## Regression risks
Low — enforcement is additive and only affects latest run in build mode. Historical artifacts untouched.
