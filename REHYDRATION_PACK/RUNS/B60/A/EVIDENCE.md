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

## Regenerated docs
```powershell
cd C:\RichPanel_GIT
python scripts\regen_doc_registry.py
python scripts\regen_reference_registry.py
python scripts\regen_plan_checklist.py
```

## Notes
- `python -m unittest scripts/test_claude_gate_review.py` from repo root failed due to module import path; reran from `scripts/` directory.

## Claude gate run (CI)
- PR: https://github.com/KevinSGarrett/RichPanel/pull/189
- Checks: https://github.com/KevinSGarrett/RichPanel/pull/189/checks
- Claude review comment: https://github.com/KevinSGarrett/RichPanel/pull/189 (latest `Claude Review` comment)
- Mode: shadow
- Model used: claude-opus-4-5-20251101
- Anthropic request/response IDs: see latest Claude Review comment (canonical marker).

## PII-safe output snippet
```
Mode: SHADOW
CLAUDE_REVIEW: PASS
Model used: claude-opus-4-5-20251101
Anthropic Request ID: (see PR comment)
Anthropic Response ID: (see PR comment)
```
