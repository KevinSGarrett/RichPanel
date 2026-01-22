# Command Log

- python -m compileall scripts backend/src
- python -m pytest -v
- python -m pytest --cov=scripts --cov=backend/src
- python scripts/run_ci_checks.py --ci (initial run failed due to uncommitted changes)
- `python scripts/run_ci_checks.py --ci` (clean run captured to VALIDATION_FULL_OUTPUT.md)
- `git checkout -b b51-validation-complete`
- `git commit -m "B51: prep validation evidence and legacy run ids"`
- `git commit -m "B51: record validation success evidence"`
- `git push -u origin b51-validation-complete`
- `gh pr create --title "B51: Complete validation evidence and legacy run ids (risk:R0)" --body-file _tmp_pr_body.md --base main --head b51-validation-complete`
