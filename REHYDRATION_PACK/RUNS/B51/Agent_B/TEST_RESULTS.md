Test Results

- python -m compileall backend/src scripts: PASS
- python -m pytest -q: PASS (370 passed, 9 subtests passed)
- python scripts/run_ci_checks.py --ci: FAIL
  - Reason: run_ci_checks detects a dirty worktree after regen.
  - Uncommitted changes at time of run included:
    - backend/src/richpanel_middleware/commerce/order_lookup.py
    - scripts/shadow_order_status.py
    - backend/tests/test_order_lookup_order_id_resolution.py
