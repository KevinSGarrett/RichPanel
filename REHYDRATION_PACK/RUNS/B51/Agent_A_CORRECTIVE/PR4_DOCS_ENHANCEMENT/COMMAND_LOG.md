# Command Log

- `python scripts/regen_doc_registry.py`
- `python scripts/regen_reference_registry.py`
- `python scripts/regen_plan_checklist.py`
- `git checkout -b b51-doc-enhancement`
- `git commit -m "B51: enhance Claude gate audit docs"`
- `git push -u origin b51-doc-enhancement`
- `gh pr create --title "B51: Enhance Claude gate audit docs (risk:R0)" --body-file _tmp_pr_body.md --base main --head b51-doc-enhancement`
