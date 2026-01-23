# Changes

## Code
- `scripts/claude_gate_review.py`: update Claude 4.5 model IDs, enforce allowlist, add CLI model override, and print proof log line.
- `.github/workflows/pr_claude_gate_required.yml`: add PR event types and write proof details to the Actions Step Summary.
- `scripts/test_claude_gate_review.py`: update model expectations, validate allowlist, and assert output keys.
- `backend/tests/test_claude_gate_model_selection.py`: add risk parsing and allowlist tests.
- `scripts/fixtures/*` + `scripts/test_claude_review_kpi_*`: refresh model IDs in fixtures/tests.

## Docs
- `docs/08_Engineering/CI_and_Actions_Runbook.md`: update model mapping + proof requirements and add local debug steps.
- `docs/08_Engineering/Claude_Gate_Audit_Proof.md`: update model mapping and example IDs.
- `REHYDRATION_PACK/PR_DESCRIPTION/05_EXAMPLES_STRONG_PR_DESCRIPTIONS.md`: update Haiku 4.5 example ID.

## Run Artifacts
- `REHYDRATION_PACK/RUNS/B54/A/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B54/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B54/A/CHANGES.md`
