# RichPanel — Bugbot + Codecov + Claude Review Suite (v3)

This pack is an **opinionated, end-to-end** documentation suite for running an **AI‑only development workflow** with:

- **ChatGPT Project Manager (PM)** → creates work plans + Cursor prompts
- **3 Cursor Agents (A/B/C)** → implement changes, tests, PRs
- **ChatGPT Assistant Manager (AM)** → performs rigorous run review + scoring (95+ gate)
- **Cursor Bugbot** → PR bug-finding review gate
- **Codecov** → coverage regression / change-risk gate
- **Claude Review (Semantic Review Agent)** → “meaning and risk” review gate (correctness/security/design)

The goal is to stop wasting cycles by running expensive gates on tiny commits, while still keeping the repo **continuously shippable** and **auditable**.

---

## What you get

- A **formal engineering policy** for AI-only development
- A **risk classification system** that drives **when** each gate runs
- A **gate matrix** that defines the exact requirements per risk level
- Detailed policies for:
  - Bugbot
  - Codecov
  - Claude review (manual + API automation)
- **PR templates**, **checklists**, **waiver templates**, and **run-report templates**
- Implementation guidance for:
  - GitHub Actions workflows
  - Secrets + environment setup
  - Cost controls + rate limit strategy
  - Audit evidence storage

---

## Quick start

1) Read **`policies/00_ENGINEERING_POLICY_AI_GATES.md`**  
   This is the canonical policy: definitions, gates, waivers, evidence rules.

2) Adopt the **risk label taxonomy**  
   See: `policies/01_RISK_CLASSIFICATION.md`

3) Drop in templates  
   Copy these files into your repo:
   - `templates/.github/pull_request_template.md` → `.github/pull_request_template.md`
   - `templates/.github/PULL_REQUEST_TEMPLATE/*.md` → `.github/PULL_REQUEST_TEMPLATE/` (optional)

4) Decide your Claude mode  
   - **Mode A (Manual)**: Use Claude Pro/Max UI for review output + paste into PR (fast to start)
   - **Mode B (Automated)**: Use Claude API in GitHub Actions (recommended for no-human workflow)
   - **Mode C (Claude Code GitHub App)**: Use official Claude Code GitHub Actions (recommended if you want @claude mentions)

   See: `tooling/CLAUDE_REVIEW_POLICY.md` and `tooling/CLAUDE_ACTION_DESIGN.md`.

5) (Recommended) Add a “Policy Gate” required status check  
   This is how you enforce risk-based requirements without making Codecov/Bugbot/Claude run on *every push*.
   See: `policies/02_GATE_MATRIX.md` and `tooling/COST_CONTROLS.md`.

---

## File map

Start here:
- `INDEX.md`

Policies:
- `policies/*`

Tool-specific policies:
- `tooling/*`

Runbooks (how PM/Agents/AM execute this):
- `runbooks/*`

Drop-in templates:
- `templates/*`

---

## Versioning

- v3 is designed to be **compatible with your current repo** (CI uses a `validate` job and uploads coverage to Codecov).
- v3 adds a **risk-based gate strategy** so Bugbot/Codecov/Claude are not wastefully run on tiny increments.

