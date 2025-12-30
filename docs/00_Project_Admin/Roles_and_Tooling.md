# Roles and Tooling

Last updated: 2025-12-22

## Purpose of this document
Clarify **who does what** in this workflow so we do not blur:
- **planning/documentation work** (this repo)
- **implementation work** (Cursor / engineering)

This is here because some waves benefit from optional validation runs, but the primary deliverable remains a **complete project development plan**.

---

## Primary roles

### Project plan manager (ChatGPT)
Primary responsibility:
- produce and maintain the **end-to-end project development plan documentation**
- keep progress tracking updated (waves, risks, decisions, open questions)
- define “build-ready” requirements, contracts, schemas, test plans, and runbooks

Outputs:
- updated documentation folder `.zip` after each update

Not in scope (unless you explicitly change scope):
- writing production code
- deploying infrastructure
- modifying Richpanel settings directly

### Builder / worker agents (Cursor)
Primary responsibility (when we start building):
- implement the plan (code, IaC, tests)
- run verification steps in the Richpanel UI / APIs
- return short, evidence-based summaries (plus diffs/artifacts)

Important:
- Cursor usage is **optional during planning**.
- If used during planning, it is only to **validate** that the plan is implementable and to expose gaps early.

---

## When we use Cursor during planning (optional)
We may optionally ask Cursor to:
- verify **tenant-specific UI capabilities** that cannot be known from docs alone
- build **small prototypes** (e.g., eval harness skeleton) to validate that the documented contracts/schemas work
- generate quick evidence that mitigations from `CommonIssues.zip` are implementable

If you prefer to **avoid Cursor during planning**, we:
- document safe defaults + fallbacks
- defer tenant verification until later waves (tracked in `Open_Questions.md`)

---

## Where optional artifacts live
Optional validation outputs are stored under:
- `reference_artifacts/`

They are:
- **non-binding** (docs remain the source of truth)
- **sanitized** (no secrets; avoid PII)
- safe to delete later without impacting the plan

---

## Operating principle
**Docs are the contract.**  
Implementation is expected to follow the docs. Any prototype or Cursor output is used to:
- confirm the docs are implementable
- improve the docs (close gaps, remove ambiguity)
