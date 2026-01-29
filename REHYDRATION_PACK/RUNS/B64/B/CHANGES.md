# Changes - B64/B

- Added OpenAI order-status intent contract + prompt builders (`backend/src/richpanel_middleware/automation/order_status_intent.py`, `backend/src/richpanel_middleware/automation/order_status_prompts.py`).
- Gated order-status automation on OpenAI intent, stored intent artifacts, and used the reply prompt for rewrite with added safety checks (`backend/src/richpanel_middleware/automation/pipeline.py`, `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`).
- Extended proof fields + tests for OpenAI response IDs, final route, and redacted ticket excerpt (`scripts/dev_e2e_smoke.py`, `scripts/test_e2e_smoke_encoding.py`, backend tests).
- Added pytest and ruff configuration to avoid repo mirror conflicts (`pytest.ini`, `ruff.toml`), plus targeted per-file ignores for pre-existing lint.
- Hardened `dev_e2e_smoke.py` ticket fetch retries and added routing excerpt fallback redaction, with longer wait support for order-status tags.
- Updated unit tests to stub order-status intent in offline contexts and to reflect new rewrite validation reasons (`backend/tests`, `scripts/test_pipeline_handlers.py`, `scripts/test_read_only_shadow_mode.py`).
- Added script-level contract tests for order-status intent and extended rewrite/e2e smoke coverage to satisfy Codecov thresholds (`scripts/test_order_status_intent_contract.py`, `scripts/test_llm_reply_rewriter.py`, `scripts/test_e2e_smoke_encoding.py`).
- Addressed Bugbot feedback by removing unreachable retry raise in `dev_e2e_smoke.py` and aligning rewrite validation test with unexpected-tracking behavior.
- Ensured intent parse failures report `order_status_intent_parse_failed:*` by not treating parse errors as gating reasons (`backend/src/richpanel_middleware/automation/order_status_intent.py`, tests).
- Prevented empty rewrite bodies from being marked applied and added coverage to enforce `empty_body` rejection (`backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`, `scripts/test_llm_reply_rewriter.py`).