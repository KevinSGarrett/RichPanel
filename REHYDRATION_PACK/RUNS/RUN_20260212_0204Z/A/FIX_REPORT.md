# Fix Report (If Applicable)

**Run ID:** RUN_20260212_0204Z  
**Agent:** A  
**Date:** 2026-02-12

## Failure observed
- error: preorder reply rendered "ship on None" when standard estimate passed
- where: build_no_tracking_reply preorder branch
- repro steps: preorder items present, standard estimate dict supplied

## Diagnosis
- likely root cause: preorder branch treated any estimate dict as preorder and read missing keys

## Fix applied
- files changed: backend/src/richpanel_middleware/automation/delivery_estimate.py
- why it works: guard preorder estimate by preorder flag; fallback ship date to constant; omit negative day windows

## Verification
- tests run: python -m unittest scripts.test_delivery_estimate; python scripts/test_pipeline_handlers.py
- results: pass
