# Changes - B64/B

- Added OpenAI order-status intent contract + prompt builders (`backend/src/richpanel_middleware/automation/order_status_intent.py`, `backend/src/richpanel_middleware/automation/order_status_prompts.py`).
- Gated order-status automation on OpenAI intent, stored intent artifacts, and used the reply prompt for rewrite with added safety checks (`backend/src/richpanel_middleware/automation/pipeline.py`, `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`).
- Extended proof fields + tests for OpenAI response IDs, final route, and redacted ticket excerpt (`scripts/dev_e2e_smoke.py`, `scripts/test_e2e_smoke_encoding.py`, backend tests).
