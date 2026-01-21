# PR Description Policies Pack (RichPanel)

This pack defines **policies, templates, and scoring rubrics** for producing **audit-quality PR titles and PR descriptions** that maximize the effectiveness of:

- **Cursor Bugbot** (review accuracy depends on clear intent + invariants + scope)
- **Codecov** (coverage outcomes improve when tests + coverage hotspots are explicit)
- **Claude review gate** (risk framing + correctness criteria + evidence pointers)

It is designed for your workflow:

- **Project Manager (ChatGPT)** defines mission, acceptance criteria, risk, and creates prompts for **3 Cursor agents**.
- Cursor agents implement changes, run tests, and capture evidence artifacts.
- **Assistant Manager (Claude Sonnet 4.5)** scores each Cursor run to a **95/100** bar.
- PR checks stack: **Bugbot + Codecov + Claude review** (risk-tiered).

---

## What “strong” means in this repo

A PR title/description is not a story. It is an **audit-quality contract**:

- What changed
- Why it changed
- What must stay true (invariants)
- How to prove it (tests + evidence)
- What could break (risk)
- How to undo it (rollback)

When PR metadata is written this way, Bugbot/Codecov/Claude can act like “smarter reviewers” because they have **ground truth** and **verification anchors**.

---

## Files in this pack

- **README.md** — this overview
- **01_PR_DESCRIPTION_POLICY.md** — non‑negotiable PR body policies (P0/P1/P2…)
- **02_PR_DESCRIPTION_TEMPLATE.md** — copy/paste template (risk-aware)
- **03_PR_DESCRIPTION_SCORING_RUBRIC.md** — PR body scoring rubric (0–100)
- **04_BUGBOT_CODECOV_CLAUDE_OPTIMIZATION.md** — how to phrase PRs to maximize tool signal
- **05_EXAMPLES_STRONG_PR_DESCRIPTIONS.md** — strong examples to imitate
- **06_AGENT_INSTRUCTIONS_FOR_GENERATING_PR_BODIES.md** — step-by-step agent instructions
- **07_PR_TITLE_SCORING_RUBRIC.md** — PR title scoring rubric (0–100)
- **08_PR_TITLE_AND_DESCRIPTION_SCORE_GATE.md** — **minimum score policy** + **self‑score gate**

---

## The key rule (minimum score gate)

Before requesting Bugbot / Codecov / Claude review:

- PR **Title** must score at or above the minimum in **07**
- PR **Description** must score at or above the minimum in **03**
- **All P0 checks** must pass (no placeholders, no PII leaks, no broken links, no escape-sequence corruption)
- PR body must list `risk:R#` + `gate:claude`, plus the Claude model and Anthropic response id (or pending link)

Details in **08_PR_TITLE_AND_DESCRIPTION_SCORE_GATE.md**.

---

## Recommended usage (agent workflow)

1. Draft **title** using the Title formula (07).
2. Draft **PR body** using the Template (02).
3. Self-score title + body (07 + 03).
4. Iterate until thresholds are met.
5. Embed the hidden **self-score block** (08).
6. Only then: request Bugbot / Codecov / Claude.

