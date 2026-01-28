# B62/C Changes

## Code
- Enforced `RICHPANEL_OUTBOUND_ENABLED=false` as a required guard in `scripts/live_readonly_shadow_eval.py`.
- Added `--max-tickets`, `--env`, `--region`, `--stack-name`, `--out`, and `--summary-md-out` to make runs reproducible.
- Added match failure buckets, tracking/ETA availability rate, and `would_reply_send` to the JSON report schema.
- Added stable report filenames (`live_shadow_report.json`, `live_shadow_summary.md`) when `--out` is used.
- Added `--allow-ticket-fetch-failures` to continue when explicit ticket IDs are stale, recording warnings instead.
- Added GraphQL fallback in `scripts/claude_gate_review.py` when PR metadata fetch hits API size limits.
- Redacted Shopify shop domain in report output to keep artifacts PII-safe.
- Deduplicated markdown report generation by sharing the builder with the proof script.

## Tests
- Updated `scripts/test_live_readonly_shadow_eval.py` to include outbound-disabled flags.
- Added coverage for `--allow-ticket-fetch-failures`.

## CI / Workflows
- Updated `.github/workflows/shadow_live_readonly_eval.yml` to enforce outbound off, use `--max-tickets`,
  and emit `live_shadow_report.json` + `live_shadow_summary.md`.
- Added support for `ticket-ids=__none__` to bypass stale secret ticket IDs in manual runs.
- Added `shopify-token-source` input to select `PROD_SHOPIFY_API_TOKEN` when admin tokens are stale.

## Docs / Artifacts
- Updated `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md` with new outputs, required flags, and gate criteria.
- Added B62/C proof artifacts under `REHYDRATION_PACK/RUNS/B62/C/PROOF/`.
- Regenerated doc registries to satisfy CI (`docs/_generated/*`, `docs/00_Project_Admin/To_Do/_generated/*`).