# B76/B Changes

- Added `docs/08_Engineering/Prod_Cutover_Switchboard.md` as the authoritative copy/paste cutover switchboard:
  - read current state commands,
  - canary-on commands (allowlisted),
  - full-on commands,
  - rollback commands with `safe_mode` precedence,
  - mandatory evidence capture commands.
- Added run artifacts under `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/`:
  - `secrets_preflight_prod.txt`
  - `sts_identity_prod.txt`
  - `sts_identity_prod_profile_attempt.txt`
  - `preflight_prod/preflight_prod.json`
  - `preflight_prod/preflight_prod.md`
- Added run documentation:
  - `REHYDRATION_PACK/RUNS/B76/B/RUN_REPORT.md`
  - `REHYDRATION_PACK/RUNS/B76/B/EVIDENCE.md`
  - `REHYDRATION_PACK/RUNS/B76/B/CHANGES.md`
