# Evidence — B60/A

## Tests run
```powershell
cd C:\RichPanel_GIT\scripts
python -m unittest test_claude_gate_review
cd C:\RichPanel_GIT
python -m unittest backend.tests.test_claude_gate_model_selection
```

## Dry run (no API call)
```powershell
cd C:\RichPanel_GIT
$env:CLAUDE_REVIEW_MODE = "structured"
python scripts\claude_gate_review.py --dry-run --fixture legacy_small
Remove-Item Env:CLAUDE_REVIEW_MODE
```

## Notes
- `python -m unittest scripts/test_claude_gate_review.py` from repo root failed due to module import path; reran from `scripts/` directory.

## PII-safe output snippet
```
Claude gate mode: structured
Mode: STRUCTURED
Risk label: risk:R2
Model used: claude-opus-4-5-20251101
Anthropic Request ID: req_fixture_legacy
Anthropic Response ID: msg_fixture_legacy
Verdict: PASS
```
