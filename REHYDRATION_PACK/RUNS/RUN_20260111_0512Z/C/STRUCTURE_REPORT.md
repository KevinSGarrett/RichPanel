# Structure Report

**Run ID:** `RUN_20260111_0512Z`  
**Agent:** C  
**Date:** 2026-01-11

## Summary
- Added shared Richpanel ticket metadata helper and wired middleware to use it; implemented reply rewriter module and GPT-5 defaults.

## New files/folders added
- `backend/src/richpanel_middleware/integrations/richpanel/tickets.py`

## Files/folders modified
- `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/automation/prompts.py`
- `backend/src/richpanel_middleware/automation/llm_routing.py`
- `backend/src/richpanel_middleware/integrations/richpanel/__init__.py`
- `backend/src/lambda_handlers/worker/handler.py`
- `scripts/run_ci_checks.py`
- `scripts/test_llm_reply_rewriter.py`
- `REHYDRATION_PACK/RUNS/RUN_20260111_0512Z/C/*`

## Files/folders removed
- None

## Rationale (why this structure change was needed)
- Centralizing ticket metadata avoids class shadowing and enables shared dedupe/normalization. GPT-5 defaults and reply rewriter module live alongside automation code. Idempotency storage adjusted to keep PII out of persisted records.

## Navigation updates performed
- `docs/INDEX.md` updated: no
- `docs/CODEMAP.md` updated: no
- registries regenerated: no
