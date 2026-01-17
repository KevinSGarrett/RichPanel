# Fix Report — RUN_20260117_0212Z

- Problem: read-only shadow mode lacked hard separation of network reads from writes; Richpanel writes could still be attempted when outbound was disabled, and planning did not pass `allow_network` through.
- Fixes:
  - Worker `allow_network` now respects `MW_ALLOW_NETWORK_READS` independent of outbound writes.
  - Richpanel client raises `RichpanelWriteDisabledError` for non-GET methods when `RICHPANEL_WRITE_DISABLED=true`, blocking writes before transport and avoiding PII in logs.
  - Pipeline order lookup receives `allow_network`, enabling shadow reads while keeping outbound mutations gated.
  - Added offline-safe unit tests and CI wiring to enforce these behaviors.
- Validation: `python scripts/run_ci_checks.py --ci` ✅ (local, clean tree). GitHub Actions/Codecov/Bugbot pending on PR #113.
