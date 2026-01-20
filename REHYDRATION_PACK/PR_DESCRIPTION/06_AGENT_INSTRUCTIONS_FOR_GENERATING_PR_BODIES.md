# Cursor Agent Instructions: Producing 95+ PR Titles + Descriptions

This document tells a Cursor agent exactly how to produce PR metadata that:
- passes all P0 policies (01)
- meets the minimum score gate (08)
- maximizes Bugbot/Codecov/Claude signal (04)

---

## Required inputs (read before drafting)

You must have these before writing the PR title/body:

1) **PM mission** and acceptance criteria  
2) **Risk level** (`risk:R0–R4`) and which gates apply  
3) The **diff summary** (files changed + key functions modified)  
4) **Tests actually run** + results (logs or command output)  
5) **Artifacts created** (REHYDRATION_PACK paths, proof JSONs, traces)  
6) Links (or pending links) for **CI**, **Codecov**, and **Bugbot**

If any item is missing, do not guess. Add a “pending — <link>” anchor or omit the claim.

---

## Step-by-step workflow (mandatory)

### Step 0 — Draft the PR title (then score it)
1) Draft using the title formula in **07**:
   - `B##: <Outcome> (<area>) (risk:R#)` or `RUN:<id> ... (risk:R#)` or `docs(...) ... (risk:R0)`
2) Score the title using **07_PR_TITLE_SCORING_RUBRIC.md**.
3) Iterate until it meets the minimum in **08**.

### Step 1 — Copy the correct template
Use:
- **02 Standard template** for `risk:R1–R4`
- **02 R0 compact template** for `risk:R0`

Do not reorder sections.

### Step 2 — Write “Summary” as outcome bullets
- 1–5 bullets
- Each bullet should describe an outcome, not a code change list
- Mention the subsystem (order-status/OpenAI/Shopify/CI gate/etc.)

### Step 3 — Write “Why” with failure mode
Include:
- Problem/risk
- Pre-change failure mode (what broke and how you saw it)
- Why this approach (tradeoffs, constraints)

### Step 4 — Write explicit invariants
“Invariants” are the rules that must remain true.

Write them as bullet points. Examples:
- Default must be OFF unless `FLAG=true`.
- No PII in proof artifacts.
- Fail-closed when env flags missing.
- GET-only outbound calls in shadow mode.

Also include “Non-goals” (what you did not change).

### Step 5 — Map changes to acceptance criteria
For each acceptance criterion:
- where it was implemented (file/function)
- what proves it (test or artifact)

Then write “What changed” as a minimal list tied to AC.

### Step 6 — Scope list (categorized) + hotspots
List files under:
- Runtime code
- Tests
- CI/workflows
- Docs/artifacts

Then add 2–5 hotspots (the files most likely to contain bugs).

### Step 7 — Test plan (exact commands)
List:
- the exact commands you ran
- any required env vars / profiles / regions
- for E2E proofs, redact identifiers in PR body if claiming PII-safe:
  - use `--ticket-number <redacted>`

### Step 8 — Results & evidence anchors
Include:
- CI: pending — link (or green — link)
- Codecov: direct PR link
- Bugbot: pending — PR link (and how to trigger)

Then list evidence paths:
- `REHYDRATION_PACK/.../RUN_REPORT.md`
- proof JSON(s)
- traces/logs

Add a minimal PII-safe proof snippet (1–6 lines).

### Step 9 — Risk & rollback
- Risk rationale: one crisp sentence (no placeholders)
- Rollback plan: actionable steps
- Failure impact: what breaks if wrong

### Step 10 — Reviewer + tool focus
Provide:
- “Please double-check” bullets (2–6)
- “Please ignore” bullets (2–6)

---

## Step 11 — P0 compliance scan (mandatory)

Before requesting review, verify the PR body has none of these:

- `???` / `TBD` / `WIP`
- stray leading backslashes like `\risk`, `\backend`, `\temperature`
- raw customer emails or message excerpts
- secrets/tokens/keys

Quick grep patterns (run locally on the PR body text):
- `\?\?\?`
- `\\risk|\\backend|\\temperature`
- `@[A-Za-z0-9._%+-]+\.[A-Za-z]{2,}` (emails)

---

## Step 12 — Self-score and embed the hidden score block (mandatory)

1) Score the title using **07**.  
2) Score the body using **03**.  
3) Confirm all P0 checks pass (**01** + **08**).  
4) Add/update the hidden block at the top of the PR body:

```html
<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=YYYY-MM-DD -->
```

If the score is below the minimum in **08**, you must revise and rescore until it passes.

---

## When to update the PR body after checks run

If Codecov or Claude posts actionable findings:
- update **Results & evidence** with the direct link and current status
- update **Reviewer focus** to mention the hotspot files
- update the **PR_QUALITY** block if the PR body changed materially

---

## Definition of done (PR metadata)

A PR is “metadata complete” when:
- Title meets gate minimum (08)
- Body meets gate minimum (08)
- All P0 policies (01) pass
- Hidden PR_QUALITY block is present and accurate
- No placeholders remain

Only then should you trigger Bugbot and run the Claude gate.

