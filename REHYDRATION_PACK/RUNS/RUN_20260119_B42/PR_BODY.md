## Objective
Strengthen the order-status ETA (no tracking) path for the canonical scenario:
- Order Monday -> ticket Wednesday
- Standard 3-5 business day shipping
- Elapsed 2 business days -> remaining 1-3 business days

## Changes
- Unit tests: delivery_estimate canonical + weekend-crossing (`test_standard_shipping_canonical_remaining_window`, `test_weekend_crossing_remaining_window`).
- Unit test: build_no_tracking_reply includes remaining window + method label (`test_no_tracking_reply_includes_remaining_window`).
- Smoke: `order_status_no_tracking_short_window` scenario; validates remaining window + Standard label, business-day-safe timestamps.
- CI: run_ci_checks includes delivery_estimate tests.
- Run artifacts under `REHYDRATION_PACK/RUNS/RUN_20260119_B42/`.

## Tests
- python scripts/test_delivery_estimate.py
- python scripts/test_pipeline_handlers.py
- python scripts/test_e2e_smoke_encoding.py
- python scripts/run_ci_checks.py --ci (locally on clean tree)
- Smoke (dev, us-east-2, ticket 1041): PASS_WEAK (expected due to redaction) — see smoke_short_window.log

## Notes
- PASS_WEAK is expected because deployed worker redacts draft bodies; validation uses computed ETA + redacted fingerprints.
