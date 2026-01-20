# PR Description Scoring Rubric (0–100)

This rubric scores the **PR body/description** (not the code).

Use it to ensure PR metadata is strong enough to maximize:
- Bugbot accuracy
- Codecov actionability
- Claude gate reliability

This rubric is paired with:
- **07_PR_TITLE_SCORING_RUBRIC.md** (title scoring)
- **08_PR_TITLE_AND_DESCRIPTION_SCORE_GATE.md** (minimum score policy)

---

## Minimum thresholds (the gate)

See **08_PR_TITLE_AND_DESCRIPTION_SCORE_GATE.md** for the authoritative minimums.

Recommended (risk-tiered):
- `risk:R0–R1`: **≥95**
- `risk:R2`: **≥97**
- `risk:R3–R4`: **≥98**

---

## Category A — Clarity and intent (0–20)

Does a reviewer/tool understand the change quickly?

- **0–5:** unclear / vague / no real summary
- **6–10:** understandable, but missing context or motivation
- **11–15:** clear summary + why, but not tied to acceptance criteria
- **16–20:** crisp outcome statement, why/risk stated, maps to acceptance criteria

Checklist:
- [ ] Summary is 1–5 concrete bullets (not a paragraph)
- [ ] “Why” explains risk/problem and pre-change failure mode
- [ ] Mentions the primary subsystem (order-status, OpenAI, Shopify, CI gate, etc.)

---

## Category B — Expected behavior & invariants (0–20)

Are the “must hold” rules explicit and testable?

- **0–5:** missing or generic (“works”, “safe”)
- **6–10:** invariants exist but not testable
- **11–15:** clear invariants but incomplete (missing safety/gate constraints)
- **16–20:** explicit, auditable, risk-aware invariants + non-goals

Checklist:
- [ ] Invariants are bullet points
- [ ] Mentions PII/safety constraints when relevant
- [ ] Mentions fail-closed behavior when relevant
- [ ] Non-goals included (what was intentionally not changed)

---

## Category C — Scope and diff navigation (0–15)

Can a reviewer find the important files quickly?

- **0–5:** no file list, or a huge undifferentiated dump
- **6–10:** files listed but not categorized
- **11–15:** scope is categorized and highlights hotspots

Checklist:
- [ ] Runtime vs tests vs docs vs CI separated
- [ ] 2–5 “hot files” or hotspots identified

---

## Category D — Test plan quality (0–15)

Can someone reproduce verification?

- **0–5:** “tests pass” only
- **6–10:** commands listed but incomplete/ambiguous
- **11–15:** exact commands + environment assumptions + key negative cases

Checklist:
- [ ] Commands are copy/paste exact
- [ ] CI-equivalent command included when applicable (`python scripts/run_ci_checks.py --ci`)
- [ ] Mentions any special setup (env vars, AWS profile, region) when relevant
- [ ] If claiming PII-safe, ticket numbers are redacted in PR body

---

## Category E — Results & evidence (0–20)

Does the PR body contain the evidence anchors the tool stack needs?

- **0–5:** no links or evidence pointers
- **6–10:** some pointers, but missing key links or unclear where proof is
- **11–15:** includes CI/Codecov/Bugbot anchors + artifact paths
- **16–20:** anchors are complete, clean, and include minimal PII-safe proof snippets

Checklist:
- [ ] CI: pending — link, or green — link
- [ ] Codecov: direct PR link included (not only checks)
- [ ] Bugbot: pending — PR link, and how to trigger
- [ ] Evidence files listed (REHYDRATION_PACK paths, proof JSONs, logs)
- [ ] Proof snippets are PII-safe and minimal

---

## Category F — Risk, rollback, reviewer focus (0–10)

Does the PR communicate risk and how to safely review?

- **0–3:** missing risk rationale and/or rollback
- **4–7:** present but weak/hand-wavy
- **8–10:** crisp risk rationale + realistic rollback + reviewer focus reduces noise

Checklist:
- [ ] Risk label and rationale (no placeholders)
- [ ] Rollback plan is actionable
- [ ] Reviewer focus includes “double-check” + “ignore” bullets

---

## Auto-fail conditions (cannot be gate-ready)

If any occur, the PR body is considered **below threshold** regardless of points:

- Missing invariants section
- Missing evidence anchors (CI/Codecov/Bugbot) or “pending” without link
- Placeholder content present (`???`, `TBD`, `WIP`)
- PII or secrets present in PR body
- Formatting corruption (escape-sequence issues, stray leading backslashes)
- Required section set is missing or reordered

---

## Fast self-scoring procedure (agent workflow)

1) Run P0 checks first (policy 01 + gate 08). If any fail → fix immediately.  
2) Score each category A–F using the checklists.  
3) If score is below threshold:
   - fix the weakest category first (usually E or B)
   - rescore
4) Add/update the hidden `PR_QUALITY` block (08).  
5) Only then request Bugbot/Codecov/Claude.

