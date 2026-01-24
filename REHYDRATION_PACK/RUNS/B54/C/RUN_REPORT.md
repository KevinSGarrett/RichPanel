# Agent Run Report

## Metadata
- **Run ID:** `b54-20260123-live-readonly-shadow`
- **Agent:** C
- **Date (UTC):** 2026-01-24
- **Worktree path:** `C:\RichPanel_GIT`
- **Branch:** `main`
- **PRs:** https://github.com/KevinSGarrett/RichPanel/pull/161, https://github.com/KevinSGarrett/RichPanel/pull/162, https://github.com/KevinSGarrett/RichPanel/pull/163, https://github.com/KevinSGarrett/RichPanel/pull/164, https://github.com/KevinSGarrett/RichPanel/pull/165, https://github.com/KevinSGarrett/RichPanel/pull/167, https://github.com/KevinSGarrett/RichPanel/pull/168, https://github.com/KevinSGarrett/RichPanel/pull/169
- **PR merge strategy:** merge commit

## Objective + stop conditions
- **Objective:** Build a safe, repeatable live read-only shadow validation run that reads PROD Richpanel + Shopify (GET/HEAD only), computes order-status logic without writes, and emits sanitized artifacts.
- **Stop conditions:** workflow dispatch exists; scripts enforce read-only guards; PII-safe report template stored in `REHYDRATION_PACK/RUNS/B54/C/PROOF/`.

## Ticket sourcing (required)
- **How obtained:** workflow dispatch used explicit ticket IDs (provided out-of-band) to bypass list endpoints.
- **Ticket reference:** stored as hashed ticket IDs in the JSON report (no raw IDs).

## What changed (high-level)
- Extended `scripts/live_readonly_shadow_eval.py` to sample tickets, enforce prod-only runs, and emit sanitized JSON/MD reports with GET/HEAD-only traces.
- Added latest-ticket sampling + sanitized output fields in `scripts/shadow_order_status.py`.
- Added workflow dispatch `shadow_live_readonly_eval.yml` that runs the evaluation with GH secrets and uploads artifacts.
- Adjusted Claude gate shadow-mode parsing to avoid action-required noise on structured JSON parse failures.
- Extracted shared ticket sampling helpers into `scripts/readonly_shadow_utils.py` and hardened workflow inputs + `boto3` install.
- Centralized `_safe_error` handling in the shared utility to avoid duplication.
- Enabled optional AWS secret resolution in the workflow when GH secrets are secret IDs.
- Added fallback to list tickets via `/api/v1/conversations` and `/v1/conversations` when `/v1/tickets` is forbidden or missing.
- Added `use-aws-secrets` workflow input to force AWS Secrets Manager resolution.
- Added `shopify-probe` flag to issue a read-only Shopify orders count GET for validation (best-effort).
- Added GH secret fallback for `PROD_SHOPIFY_API_TOKEN` when admin token secret is missing.
- Added Shopify order-number lookup fallback via `orders.json?name=` to resolve non-ID order numbers.
- Updated unit tests for new CLI flags and redaction rules.

## Commands run
- `python -m unittest scripts.test_live_readonly_shadow_eval scripts.test_shadow_order_status`
- `python scripts/test_claude_gate_review.py`

## Tests / Proof
- Workflow dispatch run: https://github.com/KevinSGarrett/RichPanel/actions/runs/21309232168
- Proof: `REHYDRATION_PACK/RUNS/B54/C/PROOF/live_readonly_shadow_eval_report.md`

## Docs impact
- Added run artifacts: `REHYDRATION_PACK/RUNS/B54/C/RUN_REPORT.md`, `EVIDENCE.md`, `CHANGES.md`.
- Updated runbook: `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`.

## Risks / edge cases considered
- Read-only guardrails fail closed if required flags are missing or incorrect.
- HTTP trace asserts GET/HEAD-only methods and stores a redacted path summary.
- No customer identifiers or message bodies are written to reports.

## Blockers / open questions
- Shopify probe returned 401 (unauthorized); confirm access token + shop domain alignment to prove successful Shopify read.

## Follow-ups
- [x] Recorded workflow run link + artifact paths.
