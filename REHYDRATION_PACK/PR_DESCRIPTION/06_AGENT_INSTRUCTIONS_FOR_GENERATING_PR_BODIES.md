# Cursor Agent Instructions: Generating High-Power PR Descriptions

This document gives step-by-step instructions for Cursor agents to produce PR descriptions that consistently score **≥95/100**.

---

## Inputs you must read before writing the PR body

1. **PM prompt / mission** (from ChatGPT PM)
2. **Acceptance criteria** (explicit checklist)
3. **Risk label** (R0–R4) and which gates apply
4. Your **diff** (files changed + key functions modified)
5. **Tests actually run** + results
6. **Artifacts created** (REHYDRATION_PACK paths, proof JSONs, logs)

---

## Output contract

You must produce:

- PR body using `02_PR_DESCRIPTION_TEMPLATE.md`
- Evidence pointers that are **valid repo paths** or **links**
- Invariants that match the PM intent and your implementation

If you cannot provide evidence, you must:

- run the missing test(s), or
- remove the claim

---

## Step-by-step procedure

### Step 1 — Extract intent and invariants from PM prompt
Create a short list:

- “Must never …”
- “Default must …”
- “In production, if missing X, then …”

This becomes the **Expected behavior & invariants** section.

### Step 2 — Map changes to acceptance criteria
Make a table (mentally or in notes):

- AC #1 -> where implemented -> test proving it

Then write **What changed** as a minimal set of bullets tied to AC.

### Step 3 — Identify hotspots
Pick 2–5 hotspots:

- top files
- top functions
- top behaviors

Put these under “Scope” and “Reviewer focus”.

### Step 4 — Test plan must reflect reality
List only what you actually ran.

- If you ran `python scripts/run_ci_checks.py --ci`, include it.
- If you ran smoke in dev/staging, include environment and run ID.

### Step 5 — Evidence must be navigable
For every major claim, add one of:

- a CI link
- a Codecov link
- a Bugbot link
- a repo path artifact

Always prefer **repo paths** for long-term auditability.

### Step 6 — Add “Please ignore” noise controls
If you regenerated doc registries or committed large run folders, explicitly write:

- “Ignore generated registries unless CI fails.”

This reduces low-signal comments.

### Step 7 — Self-score with rubric
Use `03_PR_DESCRIPTION_SCORING_RUBRIC.md`.

If <95:

- add missing invariants
- add missing links
- tighten summary
- add reviewer focus

---

## Common failure modes and fixes

### Failure mode: PR body is only 1–2 sentences
Fix: Use template; add invariants + test plan + evidence.

### Failure mode: Claims “PII-safe” but no proof
Fix: Add PII scan evidence path or redaction explanation and artifact path.

### Failure mode: “CI will pass”
Fix: Add the Actions run link (pending is fine).

---

## Optional: “PR Body Delta” checklist for edits

Before finalizing, confirm:

- [ ] Summary: outcome-based
- [ ] Why: pre-change failure mode included
- [ ] Invariants: bulleted and checkable
- [ ] Tests: commands present
- [ ] Evidence: CI + Codecov + Bugbot links
- [ ] Risk: stated and rationalized
- [ ] Rollback: explicit
- [ ] Reviewer focus: double-check + ignore

