# PR Title + PR Description Score Gate (Minimum Quality Standard)

This document defines the **minimum score requirements** for PR titles and PR descriptions.

Goal: ensure every PR metadata package is strong enough to extract the **maximum value** from:

- Bugbot
- Codecov
- Claude review gate

This is mandatory for the no-human / agent-driven workflow.

---

## Why a score gate exists

Your tooling stack is powerful, but it is only as “smart” as the **information you feed it**.

Weak PR metadata causes:
- Bugbot to comment on the wrong things
- Claude to fail gates for non-substantive reasons (typos, formatting, missing links)
- Codecov findings to be harder to action (no hotspot guidance, unclear test intent)
- Extra reruns and costly loops

A score gate prevents “avoidable failures.”

---

## Definitions

- **Title score**: scored using **07_PR_TITLE_SCORING_RUBRIC.md**
- **Body score**: scored using **03_PR_DESCRIPTION_SCORING_RUBRIC.md**
- **P0 checks**: non-negotiable conditions that **force a fail** regardless of score

---

## Recommended minimum thresholds

### Recommended (risk-tiered)
This is the best balance of speed + quality.

| Risk level | Title minimum | Body minimum |
|---|---:|---:|
| `risk:R0` (docs) | 95 | 95 |
| `risk:R1` | 95 | 95 |
| `risk:R2` | 95 | 97 |
| `risk:R3` | 95 | 98 |
| `risk:R4` | 95 | 98 |

### If you want ONE number (simpler)
Set:
- **Title ≥95**
- **Body ≥97**

This reduces tool churn on higher-risk PRs while keeping the rule simple.

---

## P0 checks (hard fail)

If any P0 check fails, the PR is **not allowed** to request review (Bugbot/Codecov/Claude) even if the numeric score is high.

### P0-A — Identity & risk correctness
- [ ] Title includes `(risk:R#)` and matches PR label/intent
- [ ] Body includes `Risk: risk:R#` exactly (no typos, no escape corruption)
- [ ] Risk rationale is present and contains **no placeholders** (no `???`)

### P0-B — Required section set
Body includes these sections (in this order):
1) Summary  
2) Why  
3) Expected behavior & invariants  
4) What changed  
5) Scope / files touched  
6) Test plan  
7) Results & evidence  
8) Risk & rollback  
9) Reviewer + tool focus

### P0-C — Evidence anchors exist (even if pending)
- [ ] CI is either linked directly or “pending — <link>”
- [ ] Codecov is linked directly (not only “checks”)
- [ ] Bugbot is linked or “pending — <PR link>” (and how to trigger)

### P0-D — No “tool-breaking” formatting
- [ ] No `???`, `TBD`, or placeholder-only PR body
- [ ] No escape-sequence corruption (avoid leading backslashes such as `\risk`, `\backend`, `\temperature`)
- [ ] File paths and flags are wrapped in backticks

### P0-E — PII and sensitive data hygiene
- [ ] No raw customer PII in PR body (emails, full ticket bodies, customer names)
- [ ] Ticket numbers / event IDs should be redacted in the PR body when the PR claims “PII-safe”
- [ ] Secrets are never pasted into PR body (keys/tokens)

### P0-F — Claude gate audit trail
- [ ] PR has `gate:claude` label applied
- [ ] PR body lists `Labels: risk:R#, gate:claude`
- [ ] PR body includes the Claude model string used
- [ ] PR body includes the Anthropic response id (or `pending — <link>` until the gate runs)

---

## The self-score requirement (mandatory)

Before requesting Bugbot/Codecov/Claude:

1. Score the **Title** using **07**
2. Score the **Body** using **03**
3. Verify all **P0 checks** above
4. If any score is below threshold, revise and rescore

### Required hidden self-score block

Add this **HTML comment** near the top of the PR body:

```html
<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=YYYY-MM-DD -->
```

Rules:
- It must be updated when the PR body/title changes.
- `p0_ok` must be true only if all P0 checks pass.

---

## Agent workflow (required)

### 1) Draft title
- Use the Title formula.
- Score it using 07.
- Iterate until it meets minimum.

### 2) Draft PR body
- Use the template (02).
- Ensure every claim has a proof pointer.
- Ensure “pending” includes a link.

### 3) Self-score and embed score block
- Score using 03.
- Fix deductions until thresholds are met.
- Add the hidden `PR_QUALITY` block.

### 4) Only then request tool review
- Trigger Bugbot (`@cursor review`) when applicable
- Wait for Codecov results
- Run Claude gate based on risk

---

## Remediation loop (when failing)

If Title/Body fails the gate:
- Do **not** request Claude or Bugbot.
- Fix PR metadata first.
- Then re-run the gate workflow.

If a tool fails due to PR metadata errors (typos, missing links, formatting corruption), treat that as a **process defect** and update this pack if needed.

