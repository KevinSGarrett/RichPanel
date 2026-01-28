# Evidence - B63/B

## Scope and safety

- CI/workflow-only changes; no production writes.
- No customer messaging.

## Claude gate summary output (workflow summary text)

From `REHYDRATION_PACK/RUNS/B63/B/PROOF/test_claude_gate_review_output.txt`:

```text
=== DRY RUN: STEP SUMMARY ===
Claude gate mode: legacy
Mode: LEGACY
Risk label: risk:R2
Model used: claude-opus-4-5-20251101
Anthropic Request ID: req_fixture_legacy
Anthropic Response ID: msg_fixture_legacy
Verdict: PASS

Copy/paste for PR description:
```

```json
{
  "model_used": "claude-opus-4-5-20251101",
  "anthropic_request_id": "req_fixture_legacy",
  "claude_response_id": "msg_fixture_legacy"
}
```

## Unit tests (Claude gate review)

```powershell
cd C:\RichPanel_GIT\scripts
python -m unittest test_claude_gate_review 2>&1 | Tee-Object -FilePath ..\REHYDRATION_PACK\RUNS\B63\B\PROOF\test_claude_gate_review_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B63/B/PROOF/test_claude_gate_review_output.txt`
- Note: error lines (missing ANTHROPIC_API_KEY / usage) are expected in negative-path tests.

## CI-equivalent (local)

```powershell
cd C:\RichPanel_GIT
python scripts\run_ci_checks.py 2>&1 | Tee-Object -FilePath REHYDRATION_PACK\RUNS\B63\B\PROOF\run_ci_checks_output.txt
```

- Output: `REHYDRATION_PACK/RUNS/B63/B/PROOF/run_ci_checks_output.txt`
- Note: doc hygiene warnings are non-strict (see log head).

## PR #200 merge evidence

- Output: `REHYDRATION_PACK/RUNS/B63/B/PROOF/pr_200_status.json`

Snippet:

```json
{"state":"MERGED","mergeCommit":{"oid":"52d94e5f04167969e9e65fb5de648e570ff1e5ad"}}
```
