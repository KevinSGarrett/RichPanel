Notes

- run_ci_checks emitted a temporary claude_gate_audit.json; deleted and re-run clean.
- Claude gate passed on PR #148 (model: claude-opus-4-5, response id: msg_014EnqTGhdxjA3Be1AiTELie, request id: req_011CXNyg4EmVTUVTJCpAxLJ6).
- Added coverage-focused tests for nested order_id extraction and shadow skip path after Codecov report.
- Removed unused conversation_id parameter from _extract_order_id per Bugbot finding.
