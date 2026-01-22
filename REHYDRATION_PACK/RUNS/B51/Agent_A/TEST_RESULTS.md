# Test Results

- python -m compileall scripts backend/src -> OK
- python -m pytest -q -> OK (354 passed, 4 subtests)
- python scripts/run_ci_checks.py --ci -> FAIL (generated files changed after regen; run folder name warnings include B51)
