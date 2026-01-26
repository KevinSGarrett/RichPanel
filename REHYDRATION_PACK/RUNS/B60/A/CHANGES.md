# B60/A Changes

## Code
- Updated `scripts/claude_gate_review.py` to print explicit mode/telemetry, add balanced-brace JSON extraction with PII-safe parse warnings, normalize request-id headers, and default unknown risk models to Opus 4.5.
- Treated structured parse failures as warnings (non-blocking) while preserving audit identifiers.
- Updated `.github/workflows/pr_claude_gate_required.yml` to include mode in the job summary.

## Tests
- Extended `scripts/test_claude_gate_review.py` and `backend/tests/test_claude_gate_model_selection.py` for JSON extraction, header parsing, and fallback model coverage.

## Docs
- Updated `docs/08_Engineering/Claude_Gate_Audit_Proof.md` with mode visibility, dashboard correlation guidance, and audit vs quality gate context.
