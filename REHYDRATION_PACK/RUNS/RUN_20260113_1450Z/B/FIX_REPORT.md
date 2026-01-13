# Fix Report

**Run ID:** RUN_20260113_1450Z  
**Agent:** B  
**Date:** 2026-01-13

## Failure observed
- error: loop-prevention removed, allowing duplicate auto-replies; smoke PASS allowed skip/escalation outcomes; deduped tag sets risked JSON serialization/ordering issues and Codecov patch red.
- where: `backend/src/richpanel_middleware/automation/pipeline.py`, `scripts/dev_e2e_smoke.py`.
- repro steps: inspect PR #94 behavior and prior smoke proof; note absence of loop guard before reply, and PASS succeeding even when skip tags present.

## Diagnosis
- likely root cause: loop guard logic was dropped while refactoring; smoke criteria only blocked skip tags added this run partially and accepted historical skip/escalation as PASS signals; dedupe_tags returns sets that were forwarded to JSON bodies, causing coverage gaps and potential serialization issues.

## Fix applied
- files changed: `automation/pipeline.py` (restore loop guard, route support on existing loop tag, sort deduped tags before JSON), `dev_e2e_smoke.py` (strict PASS: require resolved/closed or success tag added this run; fail if any skip/escalation tag added; expand skip set), tests updated (`test_pipeline_handlers.py`, `test_e2e_smoke_encoding.py`), runbook criteria updated.
- why it works: loop guard now checks ticket tags before replying and routes to support with follow-up skip/escalation tags; deduped tags are serialized as sorted lists; smoke PASS now hinges on real success signals and explicitly fails on skip/escalation additions.

## Verification
- tests run: `python -m pytest scripts/test_pipeline_handlers.py scripts/test_e2e_smoke_encoding.py`
- results: all tests pass; additional DEV proof PASS at `REHYDRATION_PACK/RUNS/RUN_20260113_1450Z/B/e2e_outbound_proof.json`.
