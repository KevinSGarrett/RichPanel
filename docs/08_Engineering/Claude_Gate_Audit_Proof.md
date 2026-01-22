# Claude Gate Audit Proof

Last updated: 2026-01-22  
Status: Canonical

## PR comment evidence (required)

The Claude Gate PR comment must include:

- Model used (explicit string)
- Anthropic Response ID
- Anthropic Request ID (from response headers)
- Token usage (input/output)
- `skip=false`

This comment is the human-readable audit trail that the gate performed a real Anthropic API call.

## Confirm the run used the intended model

1. Check the PR risk label (`risk:R0`-`risk:R4`).
2. Validate the model in the PR comment matches the mapping:
   - `risk:R0` → `claude-haiku-4-5`
   - `risk:R1` → `claude-sonnet-4-5`
   - `risk:R2` → `claude-opus-4-5`
   - `risk:R3` → `claude-opus-4-5`
   - `risk:R4` → `claude-opus-4-5`
3. If the model does not match, the gate run is invalid and must fail.

## Audit artifact (why it exists)

The workflow uploads an artifact named `claude-gate-audit` containing
`claude_gate_audit.json`. This file is a machine-readable record that enables
later verification without ambiguity.

The JSON includes:

- `pr` (PR number)
- `risk_label`
- `model`
- `response_id`
- `request_id`
- `usage` (input/output tokens)

Use this artifact to cross-check the PR comment and to reconcile usage with
the Anthropic dashboard.
