# Test Results

- python -m compileall scripts backend/src -> OK (exit 0)
- python -m pytest -v -> OK (see pytest_verbose_full.txt)
- python -m pytest --cov=scripts --cov=backend/src -> OK (see pytest_coverage_full.txt)
- python scripts/run_ci_checks.py --ci -> pending re-run after commit
