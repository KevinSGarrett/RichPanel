# Command Log

- `python scripts/audit_secrets_in_logs.py`
- `gh run view 21238528824 --log` (PR141 validate)
- `gh run view 21238528803 --log` (PR141 gate)
- `gh run view 21253500255 --log` (PR142 validate)
- `gh run view 21253521460 --log` (PR142 gate)
- `git checkout -b b51-secrets-audit`
- `git commit -m "B51: add secrets audit and CI check"`
- `git push -u origin b51-secrets-audit`
- `gh pr create --title "B51: Add secrets audit and CI enforcement (risk:R0)" --body-file _tmp_pr_body.md --base main --head b51-secrets-audit`
- `python scripts/audit_secrets_in_logs.py` (rerun after redaction fix)
