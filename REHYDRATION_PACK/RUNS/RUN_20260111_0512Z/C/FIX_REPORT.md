# Fix Report

**Run ID:** RUN_20260111_0512Z  
**Agent:** C  
**Date:** 2026-01-11

## Failure observed
- Bugbot flagged local `TicketMetadata` shadowing and GPT-4 defaults in middleware; reply rewriter needed fail-closed gating and PII-safe persistence.

## Diagnosis
- Pipeline defined its own `TicketMetadata`, bypassing shared helper and risking drift. Defaults still pointed to `gpt-4o-mini`. Idempotency storage kept payload excerpts containing customer messages. Reply rewriter missing implementation/tests.

## Fix applied
- Added shared `integrations/richpanel/tickets.py` and imported in pipeline.
- Switched prompt/routing defaults to `gpt-5.2-chat-latest`; implemented gated reply rewriter with GPT-5 defaults and risk checks.
- Updated idempotency writes to store payload fingerprints/counts (no excerpts).
- Expanded tests for rewrite gating/fallback and reran pipeline handler suite.

## Verification
- Tests run: `python scripts/test_llm_reply_rewriter.py`, `python scripts/test_pipeline_handlers.py`
- Results: pass
