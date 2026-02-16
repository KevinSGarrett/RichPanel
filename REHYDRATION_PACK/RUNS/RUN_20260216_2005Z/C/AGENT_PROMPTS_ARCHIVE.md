# Agent Prompts Archive

Archived as part of `RUN_20260216_2005Z`.

prompt-repeat-override: true

## Model + MAX mode + Cycle
- **Model used:** gpt-5.2-codex
- **MAX mode:** OFF
- **Cycle:** 1x

## Current prompts

### Agent A - B86 ETA processing + messaging updates

```markdown
Cursor Agent Prompt - Agent A (B86)

Run ID: RUN_<AUTO_UTC>
Generate with: python scripts/new_run_folder.py --now

Agent: Agent A
Task ID(s): B86-A
Goal: Implement the new ETA formulas + message updates + tests without touching AWS/prod and without any outbound customer messaging.

Hard safety rules (NON-NEGOTIABLE)
NO customer contact of any kind.
Do not run any script that sends messages.
Do not enable outbound.
Do not write/update Richpanel tickets.
NO AWS/prod changes in this run.
Do not change SSM parameters, Secrets Manager, Lambda env vars, CDK, or deploy anything.

Context (read first)
We are updating the ETA fallback logic for order status tickets without tracking, including pre-orders.

Primary runtime file:
backend/src/richpanel_middleware/automation/delivery_estimate.py

Primary scripts/tests impacted by ETA changes:
scripts/test_delivery_estimate.py (runs in CI-equivalent)
backend/tests/test_delivery_estimate_fallback.py
scripts/live_readonly_shadow_eval.py (proof signal extraction; must remain consistent with new message wording)
scripts/test_live_readonly_shadow_eval.py

CI-equivalent command:
python scripts/run_ci_checks.py --ci

New required business logic (AUTHORITATIVE)
Shipping classification
We have two processing profiles:
A) Standard / Ground (default)
Processing: 3-5 business days
Shipping transit: whatever the method window is (e.g., Standard 3-5, Ground 3-7, etc.)
B) Expedited 24h processing + 24h shipping
If the shipping method indicates rush / overnight / express / priority / next day, then:
Processing: 24 business hours (treat as 1 business day in calculations)
Shipping transit: 24 business hours (treat as 1 business day in calculations)
IMPORTANT: Expedited rule overrides parsed windows for Express/Rush.

Non-preorder ETA formula (no tracking)
delivery_window = order_date + processing_time (business days) + transit_time (business days)
Message must include: processing time, shipping method bucket/window, delivery window dates, and "in about X-Y business days".

Pre-order ETA formula (no tracking)
Pre-order detected by order tags containing "Pre-order" / "preorder" / "pre order".
release_date = order_date + 45 calendar days
delivery_window = release_date + processing_time + transit_time (business days)
Message must include: pre-order, release date, processing time, delivery window dates, and "Arrives in X-Y days".

ETA floor / cap requirement
Non-preorder ETA string must never show "0-1 business days".
If remaining_min < 1 set to 1; if remaining_max < 2 set to 2.

Invariants
Pre-order triggers only when order has preorder tag.
Tracking-present behavior unchanged.
Unknown shipping methods fail closed.

Implementation plan (Cycle 1)
Step 0 - Create run folder + branch
Step 1 - Implement processing-time + expedited overrides (runtime)
Step 2 - Update message copy to include processing + dates
Tests to update: scripts/test_delivery_estimate.py, backend/tests/test_delivery_estimate_fallback.py,
scripts/live_readonly_shadow_eval.py, scripts/test_live_readonly_shadow_eval.py

Evidence requirements
Create/update required run docs under REHYDRATION_PACK/RUNS/<RUN_ID>/A/
Include output from python scripts/run_ci_checks.py --ci

PR requirements
Risk label: risk:R3-high
Claude gate label: gate:claude
PR description template: REHYDRATION_PACK/PR_DESCRIPTION/02_PR_DESCRIPTION_TEMPLATE.md
No PII in PR body.

Agent Summary (required at end of run)
Append using REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md with:
branch name, PR number/link, last commit SHA, prompt set fingerprint.
```

### Agent B
No prompt (inactive).

### Agent C
No prompt (inactive).
