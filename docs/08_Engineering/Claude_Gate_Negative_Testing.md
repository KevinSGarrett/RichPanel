# Claude Gate Negative Testing

Last updated: 2026-01-22  
Status: Canonical

## Purpose

These tests provide **proof of fail-closed behavior** for the Claude Gate by
executing the real gate script under controlled negative conditions.

## Strategy

- Run `scripts/claude_gate_review.py` via subprocess.
- Stub external HTTP calls using `sitecustomize` to avoid real network access.
- Force failure scenarios and assert the script exits non-zero with clear errors.

## Scenarios covered

- Missing `ANTHROPIC_API_KEY`
- Invalid API key / non-200 Anthropic response
- Missing `gate:claude` label
- Missing `response_id`
- Missing request id header
- Zero token usage

## Where to find evidence

- Local output: `REHYDRATION_PACK/RUNS/B51/Agent_A_CORRECTIVE/NEGATIVE_TEST_RESULTS.md`
- Full logs: `REHYDRATION_PACK/RUNS/B51/Agent_A_CORRECTIVE/TEST_EXECUTION_LOGS/negative_tests_full.txt`
- CI runs: PR #144 checks (Negative Test Scenarios workflow)

## How to run locally

```
python -m pytest scripts/test_claude_gate_negative_scenarios.py -v
```
