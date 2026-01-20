# PR Description Scoring Rubric (0–100)

Target: **≥95/100** before requesting review.

This rubric is designed to maximize the usefulness of:

- Bugbot (needs intent + invariants + scope)
- Codecov (needs test plan + coverage expectations)
- Claude gate (needs risk framing + correctness criteria)

---

## Category A — Clarity and intent (0–20)

- 0–5: unclear / vague summary
- 6–10: understandable but missing context
- 11–15: clear problem and outcomes
- 16–20: crisp outcome-based summary + strong “why” + no ambiguity

Checklist:
- [ ] Summary is 1–3 bullets and outcome-based
- [ ] “Why” explains risk and pre-change failure mode
- [ ] Non-goals are explicit

---

## Category B — Invariants and safety constraints (0–20)

- 0–5: no invariants
- 6–10: some constraints implied
- 11–15: clear invariants but not testable
- 16–20: invariants are explicit, testable/auditable, and risk-aware

Checklist:
- [ ] Invariants listed as bullets
- [ ] PII/safety constraints stated when relevant
- [ ] “Fail-closed” stated when relevant

---

## Category C — Scope and diff navigation (0–15)

- 0–5: no file list or overwhelming dump
- 6–10: files listed but not categorized
- 11–15: categorized scope (runtime/tests/docs/CI) with key hotspots

Checklist:
- [ ] Runtime vs tests vs docs vs CI separated
- [ ] Hot files called out

---

## Category D — Test plan quality (0–15)

- 0–5: “tests pass” only
- 6–10: commands included but incomplete
- 11–15: exact commands + environment assumptions + key negative cases

Checklist:
- [ ] Commands are copy/paste exact
- [ ] Mentions edge cases / negative tests where relevant

---

## Category E — Evidence completeness (0–20)

- 0–5: none
- 6–10: artifacts but not linked
- 11–15: CI + artifacts linked
- 16–20: CI + Codecov + Bugbot + proof artifacts + pointers to key logs

Checklist:
- [ ] CI link present
- [ ] Codecov link present
- [ ] Bugbot link or pending link present
- [ ] Artifact paths are present and valid

---

## Category F — Risk, rollback, and reviewer focus (0–10)

- 0–3: missing risk/rollback
- 4–7: risk/rollback present but light
- 8–10: risk rationale + rollback steps + reviewer focus reduces noise

Checklist:
- [ ] Risk label and rationale
- [ ] Rollback plan
- [ ] Reviewer focus: “double-check” + “ignore” bullets

---

## Auto-fail conditions
If any of these occur, the PR description is considered **<95** automatically:

- Missing invariants section
- Missing CI link (or pending link)
- Claims safety (PII safe, read-only, default off) without evidence pointers
- Placeholder-only PR body

