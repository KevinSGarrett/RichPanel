# B75/A Run Report — Tracking Link Generation Fix

## Objective
Fix tracking reply generation so a deterministic carrier URL is used when `tracking_url` is missing but carrier + tracking number exist.

## Preconditions (Required)
- AWS dev account verified (Account=151124909266)
- Secrets preflight executed (dev)

## Implementation Summary
- Added `build_tracking_url()` with carrier normalization and official carrier URL templates.
- Wired `build_tracking_reply()` to use `tracking_url` if present or generate one deterministically.
- Added unit tests for carrier variants, URL encoding, unknown carrier, and preservation of existing `tracking_url`.

## Commands Executed (redacted)
```
aws sso login --profile rp-admin-dev
aws sts get-caller-identity --profile rp-admin-dev
python scripts/secrets_preflight.py --env dev --profile rp-admin-dev --region us-east-2 \
  --out REHYDRATION_PACK/RUNS/B75/A/PROOF/secrets_preflight_dev.json
python scripts/test_delivery_estimate.py
```

## Tests
- `python scripts/test_delivery_estimate.py` (includes new tracking URL tests)
- `python -m pytest backend/tests/test_tracking_link_generation.py`

## Artifacts
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/secrets_preflight_dev.json`
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/tracking_url_unit_proof.json`
- `REHYDRATION_PACK/RUNS/B75/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B75/A/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B75/A/PR_DESCRIPTION.md`
