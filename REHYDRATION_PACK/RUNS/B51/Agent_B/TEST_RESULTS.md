Test Results

- python -m compileall backend/src scripts: PASS
- python -m pytest -q: PASS (378 passed, 9 subtests passed)
- python scripts/run_ci_checks.py --ci: PASS
  - Earlier run failed while coverage fixes were uncommitted; reran clean.
