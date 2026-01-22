# Command Log

- python -m compileall scripts backend/src
- python -m pytest -v
- python -m pytest --cov=scripts --cov=backend/src
- python scripts/run_ci_checks.py --ci (initial run failed due to uncommitted changes)
- `python scripts/run_ci_checks.py --ci` (clean run captured to VALIDATION_FULL_OUTPUT.md)
