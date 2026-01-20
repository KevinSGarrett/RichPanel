# PR Title + Description Policy (RichPanel)

This document defines **mandatory policies** for PR titles and PR descriptions in the RichPanel repo.

These policies exist to:

1. Make PR checks (Bugbot / Codecov / Claude) **more accurate**.
2. Make reviews **faster** by eliminating ambiguity and guesswork.
3. Provide **auditability** (what was intended, what was proven, where the evidence lives).
4. Prevent “avoidable gate failures” caused by typos, missing links, or formatting corruption.

This policy is paired with:
- **07_PR_TITLE_SCORING_RUBRIC.md** (title scoring)
- **03_PR_DESCRIPTION_SCORING_RUBRIC.md** (body scoring)
- **08_PR_TITLE_AND_DESCRIPTION_SCORE_GATE.md** (minimum score gate)

---

## Scope

This policy governs:
- PR **title**
- PR **body/description** (the “PR description” field)

This policy does **not** govern:
- commit message format
- branch naming conventions
- code style conventions

---

## Non‑negotiable rules (P0)

### P0‑1 — No placeholders without links
Forbidden:
- “CI will pass”
- “Codecov pending”
- “Bugbot pending”
- “waiting for checks”
…if there is **no link** to the relevant page/run.

Required format examples:
- `CI: pending — <checks link or run link>`
- `Codecov: pending — <Codecov PR link>`
- `Bugbot: pending — <PR link> (trigger via @cursor review)`

Rationale: tools and reviewers need **anchors**, even when pending.

---

### P0‑2 — Risk must be consistent and correctly formatted
- Title must include `(risk:R#)` with `R0–R4`.
- Body must include `Risk: risk:R#` exactly.
- Risk rationale must be present and must not contain placeholders (`???`, `TBD`, `WIP`).

Rationale: the Claude gate depends on risk; a typo can cause an unnecessary FAIL.

---

### P0‑3 — Required section set (PR body)
Every PR body must include these sections (in this order):

1) Summary  
2) Why  
3) Expected behavior & invariants  
4) What changed  
5) Scope / files touched  
6) Test plan  
7) Results & evidence  
8) Risk & rollback  
9) Reviewer + tool focus  

Exception: **docs-only / risk:R0** may use the R0 compact template (02), but must still include:
- invariants (even for docs-only: e.g., “no runtime behavior changed”)
- evidence anchors (CI/Codecov/Bugbot can be “N/A” only when truly N/A)

---

### P0‑4 — No tool-breaking formatting
Avoid formatting that causes parsing problems or hidden corruption:

- Do not prefix content with stray backslashes (e.g., `\risk`, `\backend`, `\temperature`).
  - GitHub/markdown can interpret sequences like `\r` or `\t` in unexpected ways.
- Wrap file paths, flags, env vars, secret names, and commands in backticks:
  - `backend/src/...`
  - `OPENAI_LOG_RESPONSE_EXCERPT`
  - `python scripts/run_ci_checks.py --ci`

---

### P0‑5 — PII / secrets hygiene
The PR body must not contain:
- customer emails or names
- raw ticket bodies / customer message excerpts
- secrets, tokens, keys

If the PR claims “PII-safe proofs”, then the PR body must not include raw identifiers (ticket numbers, event IDs).
Use `<redacted>` in the PR body and store specifics in run artifacts.

---

### P0‑6 — Self-score gate is mandatory
Before requesting Bugbot / Codecov / Claude:
- Title must meet the minimum score in **07**.
- Body must meet the minimum score in **03**.
- All P0 rules above must be satisfied.

Add the hidden `PR_QUALITY` block described in **08**.

---

## Strong requirements (P1)

### P1‑1 — “Invariants” must be explicit and auditable
“Invariants” are the rules that must stay true after the change. They must be:
- written as bullet points
- testable or auditable

Examples:
- Default must be OFF (`OPENAI_LOG_RESPONSE_EXCERPT` off unless set).
- Shadow mode must never issue POST/PUT/PATCH/DELETE.
- Proof JSON must not contain raw PII fields.

---

### P1‑2 — Every claim must be provable
If the PR body claims any of the following, it must include evidence pointers:

- “default off”
- “PII safe”
- “GET only”
- “no writes”
- “PASS_STRONG”
- “fails closed”

Evidence pointers can be:
- test commands + logs
- Codecov/CI links
- artifact paths (`REHYDRATION_PACK/...`)
- trace/log files (e.g., HTTP trace JSON)

---

### P1‑3 — Scope must be categorized and navigable
List files touched and categorize them:
- Runtime code
- Tests
- CI/workflows
- Docs/artifacts

Also call out 2–5 “hot files” that deserve review attention.

---

### P1‑4 — Reviewer + tool focus must reduce noise
Provide two bullet lists:
- “Please double-check” (2–6 bullets)
- “Please ignore” (generated files, registries, artifacts, etc.)

Rationale: fewer irrelevant comments; faster review; fewer loops.

---

## Title requirements (quick checklist)

A high-quality title:
- has a recognized prefix (`B##:`, `RUN:`, `docs(...)`)
- names the outcome and the main subsystem
- includes `(risk:R#)`
- avoids vague verbs and placeholders

Use **07_PR_TITLE_SCORING_RUBRIC.md**.

