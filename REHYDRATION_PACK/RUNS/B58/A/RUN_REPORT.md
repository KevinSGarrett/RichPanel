# Run Report — B58/A

## Metadata
- Date: 2026-01-25
- Run ID: `RUN_20260125_0130Z`
- Branch: `b58/operator-reply-send-message`
- Workspace: `C:\RichPanel_GIT`

## Objective
Implement customer-visible outbound replies for email tickets using `/send-message` and remove the OpenAI routing force-primary threshold bypass.

## Summary
- Added email-channel operator reply path with author resolution and routing-on-failure tags.
- Preserved comment-based reply for non-email tickets and added deterministic path tags.
- Removed `force_primary` confidence threshold bypass in LLM routing.
- Added unit tests and a concise outbound reply path doc.

## Tests
- `python scripts\test_pipeline_handlers.py` (PASS)
- `python scripts\test_llm_routing.py` (PASS)
- `python scripts\test_e2e_smoke_encoding.py` (PASS)
- `python scripts\run_ci_checks.py --ci` (see `REHYDRATION_PACK/RUNS/B58/A/CI_RUN_OUTPUT.txt`)

## Sandbox proof (completed)
- Deployed dev stack via GitHub Actions (`deploy-dev.yml`, run `21338123425`).
- Set `RICHPANEL_BOT_AUTHOR_ID` on `rp-mw-dev-worker` (id hash recorded; no PII).
- Created fresh email tickets and ran `dev_e2e_smoke.py` with `--require-send-message` and `--require-operator-reply` (and `--no-require-outbound`).
- Proof artifact: `REHYDRATION_PACK/RUNS/B58/A/PROOF/order_status_email_sandbox_proof.json` (PASS_STRONG).