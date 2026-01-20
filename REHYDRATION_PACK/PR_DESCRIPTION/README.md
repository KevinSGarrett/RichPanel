# PR Description Policies Pack (RichPanel)

This pack defines **policies, templates, and scoring rubrics** for writing **bulletproof PR descriptions** that maximize the effectiveness of:

- **Cursor Bugbot** (static PR review + inline comments)
- **Codecov** (coverage + patch coverage expectations)
- **Claude review gate** (risk-tiered model review)

It is **specifically** designed for your workflow:

- **PM (ChatGPT)** defines mission, acceptance criteria, risk, and creates prompts for **3 Cursor agents**.
- Cursor agents implement, test, and produce evidence artifacts.
- **Assistant manager (Claude Sonnet 4.5)** evaluates each agent run to a **95/100** bar.
- PR checks stack: **Bugbot + Codecov + Claude review** (risk-tiered).

## Files

1. **01_PR_DESCRIPTION_POLICY.md** — non-negotiable rules and required sections.
2. **02_PR_DESCRIPTION_TEMPLATE.md** — copy/paste template (risk-aware variants).
3. **03_PR_DESCRIPTION_SCORING_RUBRIC.md** — how to score PR descriptions 0–100 (target ≥95).
4. **04_BUGBOT_CODECOV_CLAUDE_OPTIMIZATION.md** — how to write PR text to make each tool smarter.
5. **05_EXAMPLES_STRONG_PR_DESCRIPTIONS.md** — annotated examples for common PR types.
6. **06_AGENT_INSTRUCTIONS_FOR_GENERATING_PR_BODIES.md** — step-by-step instructions for Cursor agents.

## How to use

- Cursor agents MUST use the template in **02** and comply with policies in **01**.
- Before opening/merging, self-score using **03**. The description should be **≥95/100**.
- Use **04** when you want to maximize Bugbot/Codecov/Claude signal.

## Principle

A PR description is not a story. It is an **audit-quality contract**:

- What changed
- Why it changed
- What must stay true (invariants)
- How to prove it (tests/evidence)
- What could break (risks)
- How to undo it (rollback)

