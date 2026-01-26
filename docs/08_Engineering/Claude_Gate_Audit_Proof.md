# Claude Gate Audit Proof

Last updated: 2026-01-26  
Status: Canonical

## PR comment evidence (required)

The Claude Gate PR comment must include:

- Mode (`Mode: LEGACY|SHADOW|STRUCTURED`)
- Model used (explicit string)
- Anthropic Response ID
- Anthropic Request ID (from response headers)
- Token usage (input/output)
- `skip=false`

This comment is the human-readable audit trail that the gate performed a real Anthropic API call.

## How to verify audit proof (step-by-step)

1. Confirm the PR has both `gate:claude` and exactly one `risk:R*` label.
2. Locate the **Claude Review** PR comment and verify it includes:
   - `Mode: STRUCTURED`
   - `Model used: claude-opus-4-5-20251101`
   - `Anthropic Response ID: msg_xxx`
   - `Anthropic Request ID: req_xxx`
   - `Token Usage: input=1234, output=56`
   - `skip=false`
3. Open the GitHub Actions run for **claude-gate-check** and download the
   `claude-gate-audit` artifact.
4. Compare the artifact JSON fields with the PR comment to ensure they match.
5. If any field is missing or mismatched, treat the run as invalid and re-run the gate.

Example PR comment (redacted):

```
Claude Review (gate:claude)
Mode: STRUCTURED
CLAUDE_REVIEW: PASS
Risk: risk:R2
Model used: claude-opus-4-5-20251101
Anthropic Response ID: msg_xxx
Anthropic Request ID: req_xxx
Token Usage: input=1234, output=56
skip=false
```

## Job summary fields (fast verification)

The workflow job summary for **claude-gate-check** lists:

- Mode
- Risk label
- Model used
- Anthropic Request ID
- Anthropic Response ID

Use the summary when you need quick confirmation without opening the PR comment.

## Confirm the run used the intended model

1. Check the PR risk label (`risk:R0`-`risk:R4`).
2. Validate the model in the PR comment matches the mapping:
   - `risk:R0` → `claude-haiku-4-5-20251001`
   - `risk:R1` → `claude-sonnet-4-5-20250929`
   - `risk:R2` → `claude-opus-4-5-20251101`
   - `risk:R3` → `claude-opus-4-5-20251101`
   - `risk:R4` → `claude-opus-4-5-20251101`
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

## Correlating with the Anthropic dashboard

Use either `Anthropic Request ID` or `Anthropic Response ID` from the PR comment
or job summary. These identifiers map directly to the Anthropic dashboard logs
for the API call and are the preferred way to reconcile usage or latency.

## Audit check, not a quality gate

The Claude gate exists to create an auditable trace of the model call and its
telemetry. Treat it as an audit check: it confirms that the model was called,
captures identifiers for correlation, and surfaces findings. It is not a
replacement for human review or CI quality gates.

## Failure mode catalog (fail-closed)

The gate must **fail closed** if any of the following occur:

- Missing `gate:claude` label
- Missing `risk:R*` label or multiple risk labels
- Missing `ANTHROPIC_API_KEY`
- Anthropic API non-200 response
- Missing `response_id` in the Anthropic response
- Missing request id in response headers
- Missing or zero token usage

Structured parse failures are reported as warnings and should be investigated,
but they do not block the gate on their own.

## Troubleshooting

- **PR comment missing fields:** Inspect `claude-gate-audit` and re-run the gate.
- **Model mismatch:** Ensure the risk label matches the model mapping.
- **Missing request id:** Verify response headers include `request-id`/`x-request-id`.
- **Token usage missing/zero:** Treat as failed; the gate requires usage to be present.
