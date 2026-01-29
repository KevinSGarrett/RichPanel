# B63/C Changes

## Code
- Filtered schema key paths in `scripts/live_readonly_shadow_eval.py` to ignore noisy IDs/timestamps/pagination and stop descent into volatile subtrees (comments, tags, custom fields, metadata).
- Added `schema_key_stats` to the summary payload for drift triage.
- Excluded `ticket_fetch_failed` from drift-watch API error rate (still surfaced via `run_warnings`).

## Tests
- Added drift-watch fixtures that ignore noisy schema-only changes and still alert on real contract drift.
- Added coverage ensuring `ticket_fetch_failed` does not inflate API error rate.

## Docs
- Documented filtered schema drift and `schema_key_stats` in `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`.
