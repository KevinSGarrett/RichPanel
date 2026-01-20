# Optimizing PR Descriptions for Bugbot, Codecov, and Claude

This guide explains **what each tool needs** and how to write PR descriptions that make them “smarter”.

---

## 1) Bugbot optimization

Bugbot reviews the PR diff and surrounding context. It becomes dramatically more useful when the PR description provides:

### A) Explicit intent
Write the intent in unambiguous language:

- “This must never log PII.”
- “Default must be OFF.”
- “Production must fail-closed.”
- “Shadow mode must be GET-only.”

Bugbot can then evaluate your diff against those requirements.

### B) Invariants as checkable bullets
Good invariants are:

- Specific
- Testable or auditable
- Tied to code paths

Bad invariants are subjective:

- “Should be safe”
- “Seems correct”

### C) “Tool focus” section
Bugbot will sometimes comment on generated files, formatting, or low-value diffs.
Use:

- “Please ignore: generated registries unless CI fails.”
- “Please focus: `pipeline.plan_actions()` gating logic and the new tests proving it.”

### D) Threat model hints (R3/R4)
If risk is high, include:

- what attacker/user behavior you’re guarding against
- what data must not be written/logged
- what happens if flags are missing

---

## 2) Codecov optimization

Codecov is only “smart” if the PR description helps humans interpret coverage results.

### A) Explicit coverage expectation
Include a statement like:

- “Patch coverage must be green; new branches in `X` are covered by tests A/B/C.”

### B) Link tests to lines/branches
Write:

- “New branch: `if missing_order_context:` covered by `test_missing_order_id_no_reply`.”

### C) Declare intentional exclusions
If a line is intentionally untested (rare), state:

- “This error path is unreachable in production because X; we assert via integration test Y.”

(Prefer adding tests instead of exclusions.)

---

## 3) Claude review optimization

Your Claude gate is risk-tiered. Claude becomes more reliable when your PR body includes:

### A) A correctness contract
- define acceptance criteria
- define what constitutes “correct” vs “wrong”

Example:

- “Correct: no auto-reply when order context is missing; route to support team.”
- “Incorrect: any path that auto-closes without verified context.”

### B) Explicit edge cases
List the known tricky cases:

- missing order_id
- empty string values
- weekend-crossing ETA calculations
- retry behaviors
- safe_mode true

### C) Safety / PII declaration with proof
- “PII-safe artifacts only — proof JSON stores fingerprints, no raw emails.”

and link:

- PII scan output
- artifact file paths

### D) Minimal reviewer search cost
Claude and humans should not need to infer “where to look”. Provide:

- hotspot files
- key functions
- tests that prove invariants

---

## 4) Writing style that improves all tools

### A) Prefer declarative statements
- “Default OFF. Enabled only when `FLAG=true`.”

### B) Prefer exact commands and exact paths
- `python scripts/run_ci_checks.py --ci`
- `REHYDRATION_PACK/RUNS/.../e2e_outbound_proof.json`

### C) Tie each claim to an evidence pointer
- Claim: “GET-only”
- Evidence: `artifacts/prod_readonly_shadow_eval_http_trace.json` contains only GET.

### D) Reduce noise
If your repo regenerates indices, say so and direct tools to focus on non-generated files.

