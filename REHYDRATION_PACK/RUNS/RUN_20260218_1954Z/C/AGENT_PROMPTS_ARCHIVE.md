# Agent Prompts Archive

Archived as part of `RUN_20260218_1954Z`.

---

# Current Cursor Agent Prompts (build mode)

prompt-repeat-override: true

## Model + MAX mode + Cycle
- **Model used:** gpt-5.2-codex
- **MAX mode:** OFF
- **Cycle:** 1×

---

## Current prompts

### Agent C — B91-C (OpenAI reply rewrite model in CDK)

```markdown
# Cursor Agent Prompt — Agent C (B91)

Run ID: RUN_<AUTO_UTC> (generate with python scripts/new_run_folder.py --now)
Agent: C
Task ID(s): B91-C
Primary goal: Enable GPT-5.2 for reply rewriting in AWS via OPENAI_REPLY_REWRITE_MODEL and deploy safely with hard evidence (no customer contact).

Hard Safety Rules (NON-NEGOTIABLE)

NO customer contact

Do not send replies, do not add public notes, do not close tickets, do not tag tickets, do not write to Richpanel.

NO prod writes to Richpanel/Shopify

All verification must be read-only. Use the repo’s shadow / read-only eval tooling and GitHub workflows designed for no-write runs.

Do not weaken any safety/validation guardrails

No changes to rewrite validation rules in llm_reply_rewriter.py (URLs, tracking tokens, ETA-window preservation, internal-tag rejection).

AWS changes are allowed only in the form of CDK-managed deployments

No manual Lambda-console edits.

Before any prod deploy happens, prod must be put into “no-contact” mode

If the run requires human toggles (SSM safe_mode / automation_enabled), coordinate but do not proceed until verified safe.

Context / What is already done (read this first)

B89 (merged PR #259):

Customer first-name + customer message excerpt passed to rewrite prompt

Deterministic greeting/signature enforcement

OPENAI_REPLY_REWRITE_TEMPERATURE support in code

B90 (merged PR #260):

Deterministic Key Details block for ETA/no-tracking replies

Prompt + pipeline enforcement to preserve it through rewrite

Tests updated/added

What is NOT done yet (this run):

AWS/CDK does not set OPENAI_REPLY_REWRITE_MODEL → rewrite currently falls back to OPENAI_MODEL (prod is gpt-5.2-chat-latest).

No prod deployment evidence proving rewrite runs using gpt-5.2.

This run fixes that.

AWS accounts / environments (MUST use correct account)

From infra/cdk/cdk.json context:

dev: 151124909266 (us-east-2)

staging: 260475105304 (us-east-2)

prod: 878145708918 (us-east-2) ✅ this is the target for final rollout

You MUST verify active AWS identity before any deploy steps:

aws sts get-caller-identity

Hard requirement: Account must equal 878145708918 for prod verification steps.

Objective (B91-C)

Add AWS/CDK env vars to the prod worker Lambda so reply rewrite uses:

OPENAI_REPLY_REWRITE_MODEL = gpt-5.2

(Optional but recommended) OPENAI_REPLY_REWRITE_TEMPERATURE = 0.2
```
