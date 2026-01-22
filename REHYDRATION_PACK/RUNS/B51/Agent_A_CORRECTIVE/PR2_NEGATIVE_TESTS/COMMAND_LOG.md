# Command Log

- `python -m pytest scripts/test_claude_gate_negative_scenarios.py -v`
- `git checkout -b b51-negative-test-demonstrations`
- `git commit -m "B51: add claude gate negative scenario tests"`
- `git push -u origin b51-negative-test-demonstrations`
- `gh pr create --title "B51: Demonstrate Claude gate fail-closed scenarios (risk:R1)" --body-file _tmp_pr_body.md --base main --head b51-negative-test-demonstrations`
- `python -m pytest scripts/test_claude_gate_negative_scenarios.py -v` (rerun after updates)
