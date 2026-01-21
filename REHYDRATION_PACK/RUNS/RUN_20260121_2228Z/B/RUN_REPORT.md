# RUN REPORT — B

## What changed
- Added Richpanel client safety unit tests covering prod/staging read-only defaults, env overrides, and dry-run vs write-disable behavior.
- Added explicit Richpanel env var contract to the production read-only shadow mode runbook.

## As-is behavior (Richpanel safety)
- Default `read_only` when caller passes none: `RichpanelClient._resolve_read_only` checks `RICHPANEL_READ_ONLY`/`RICH_PANEL_READ_ONLY`, otherwise returns `self.environment in READ_ONLY_ENVIRONMENTS`.
- Environments that default to read-only: `READ_ONLY_ENVIRONMENTS = {"prod", "production", "staging"}`.
- Env var overrides: `RICHPANEL_READ_ONLY`/`RICH_PANEL_READ_ONLY` override read-only; `RICHPANEL_WRITE_DISABLED` is enforced by `RichpanelClient._writes_disabled`.
- Write-disabled POST/PUT/PATCH/DELETE behavior: `RichpanelClient.request` raises `RichpanelWriteDisabledError("Richpanel writes are disabled; request blocked")` before transport I/O.

## Tests
### pytest -q
```
331 passed, 4 subtests passed in 19.76s
```

### python scripts/run_ci_checks.py --ci
Result: failed due to uncommitted changes after regen.
```
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
```

## Docs excerpt (env var contract)
Path: `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
```
#### Live read-only shadow runs (production data, no writes)
- `RICHPANEL_ENV=prod`
- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `MW_OUTBOUND_ENABLED=false`
#### Go-live (intentional outbound)
- `RICHPANEL_READ_ONLY=false`
- `RICHPANEL_OUTBOUND_ENABLED=true`
- `MW_OUTBOUND_ENABLED=true`
```

## PR + gates
- PR: not created in this run.
- Labels: not applied in this run.
- Claude gate response_id: not available in this run.
