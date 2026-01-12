# Fix Report

**Run ID:** RUN_20260112_0408Z  
**Agent:** B (Engineering)  
**Date:** 2026-01-12

## Failure observed
- **Error:** PII leak in proof JSON - URL-encoded email/message-id exposed in `path` fields
- **Where:** `REHYDRATION_PACK/RUNS/RUN_20260112_0259Z/B/e2e_outbound_proof.json` (lines 83, 95)
- **Repro steps:** Run smoke test with `--apply-test-tag` on ticket 1023 (which has email-style ID)

## Diagnosis
- **Root cause:** `_fetch_ticket_snapshot()` stored raw API path containing ticket ID, and Richpanel uses email/message-id as ticket ID format. The raw path was not sanitized before being written to proof JSON.

## Fix applied
- **Files changed:**
  - `scripts/dev_e2e_smoke.py` - Added `_redact_path()`, `_sanitize_tag_result()`, `_check_pii_safe()`
  - `docs/08_Engineering/CI_and_Actions_Runbook.md` - Added PII-safe proof note
- **Why it works:**
  - Paths are now redacted to use placeholders instead of raw ticket IDs
  - Safety assertion scans proof JSON for PII patterns before writing

## Verification
- **Tests run:** `python scripts/run_ci_checks.py --ci`, PII pattern scan
- **Results:** PASS; no PII patterns found in proof JSON
