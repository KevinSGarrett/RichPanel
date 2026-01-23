# Golden Legacy Output Sample

This file is a **reference snapshot** of what `CLAUDE_REVIEW_MODE=legacy` output should look like.

Purpose:
- Give Cursor (and reviewers) a concrete “golden” string to use in **regression tests**.
- Prevent accidental drift in legacy mode while Wave 1–2 add structured scoring.

> Treat this as a **contract**: if legacy mode changes, it should be an intentional decision with a documented reason.

---

## What “legacy mode” is in your repo

In the current baseline `scripts/claude_gate_review.py`:
- Claude is instructed to output a plain text payload with:
  - `VERDICT: PASS|FAIL`
  - `FINDINGS:` bullets (up to 5)

The workflow then posts a PR comment formatted like:

```text
<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: LEGACY
CLAUDE_REVIEW: <PASS|FAIL>
Risk: <risk:R0..risk:R4>
Model used: <anthropic model name>
skip=false
Response model: <anthropic model name>
Anthropic Response ID: <msg_...>   # if present
Anthropic Request ID: <req_...>    # if present
Token Usage: input=<n>, output=<n> # if present

Top findings:
- <bullet>
- <bullet>
```

---

## Golden sample A — PASS with no findings

### A1) Example *raw Claude model output* (legacy contract)
```text
VERDICT: PASS
FINDINGS:
- No issues found.
```

### A2) Example *PR comment body* (what the script posts)
```text
<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: LEGACY
CLAUDE_REVIEW: PASS
Risk: risk:R2
Model used: claude-opus-4-5-20251101
skip=false
Response model: claude-opus-4-5-20251101
Anthropic Response ID: msg_0123456789abcdef
Anthropic Request ID: req_0123456789abcdef
Token Usage: input=21814, output=18

Top findings:
- No issues found.
```

---

## Golden sample B — FAIL with 2 findings

### B1) Example *raw Claude model output* (legacy contract)
```text
VERDICT: FAIL
FINDINGS:
- Potential shadow-mode write: outbound mutation path appears unguarded in `ShipStationClient.create_label(...)`.
- Missing idempotency key / dedupe token on shipment creation path (duplicate-create risk on retries).
```

### B2) Example *PR comment body* (what the script posts)
```text
<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: LEGACY
CLAUDE_REVIEW: FAIL
Risk: risk:R4
Model used: claude-opus-4-5-20251101
skip=false
Response model: claude-opus-4-5-20251101
Anthropic Response ID: msg_deadbeefcafefeed
Anthropic Request ID: req_deadbeefcafefeed
Token Usage: input=25000, output=240

Top findings:
- Potential shadow-mode write: outbound mutation path appears unguarded in `ShipStationClient.create_label(...)`.
- Missing idempotency key / dedupe token on shipment creation path (duplicate-create risk on retries).
```

---

## How to use this in a unit test (recommended)

In Wave 1, add a regression unit test that asserts legacy-mode formatting does not drift.

Suggested approach:
- Call the legacy comment formatter with deterministic inputs.
- Compare to the exact expected string (including newlines).

