# B60/A Changes

## Code
- Updated `scripts/claude_gate_review.py` to print explicit mode/telemetry, add balanced-brace JSON extraction with PII-safe parse warnings, normalize request-id headers, and default unknown risk models to Opus 4.5.
- Treated structured parse failures as warnings (non-blocking) while preserving audit identifiers.
- Expanded parse-error redaction patterns to cover emails, phone numbers, addresses, and long numeric sequences.
- Emitted a warning when an unknown risk label defaults to Opus 4.5.
- Updated `.github/workflows/pr_claude_gate_required.yml` to include mode in the job summary.

## Tests
- Extended `scripts/test_claude_gate_review.py` and `backend/tests/test_claude_gate_model_selection.py` for JSON extraction, header parsing, fallback model coverage, escape-sequence handling, and additional redaction cases.

## Docs
- Updated `docs/08_Engineering/Claude_Gate_Audit_Proof.md` with mode visibility, dashboard correlation guidance, and audit vs quality gate context.
- Regenerated `docs/_generated/*` registries after doc updates.
