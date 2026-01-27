# B61/B Changes

## Code
- Added negative-case scenarios to `scripts/dev_e2e_smoke.py` with proof fields for intent, outbound attempts, support routing, and order-match failure reasons.
- Added allowlist configuration detection + SKIP proof output for allowlist-blocked scenarios, with tag polling to capture delayed allowlist tags.
- Added unit tests for new proof helpers, skip classification, allowlist config parsing/error paths, payload building, and `--fail-on-outbound-block` behavior in `scripts/test_e2e_smoke_encoding.py`.

## Artifacts
- Planned proof outputs in `REHYDRATION_PACK/RUNS/B61/B/PROOF/` for non-order-status, no-match, and allowlist-blocked scenarios.
