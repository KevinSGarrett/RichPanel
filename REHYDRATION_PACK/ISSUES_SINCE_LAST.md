# Issues Since Last Rehydration

Last updated: 2025-12-30 (Wave F15 → B00)

## Resolved
- **GitHub CLI not available in PATH after install** → fixed by refreshing PATH in the session (`$env:Path = ...Machine + ...User`).
- **CI failure: missing `config/.env.example`** → tracked the file and updated `.gitignore` to allow committing example env files.
- **CI failure: generated artifacts changing after regen** → made regen deterministic across platforms/timezones:
  - `regen_doc_registry.py` now sorts docs by a canonical POSIX path key.
  - `regen_reference_registry.py` now sorts references by POSIX path, normalizes newline handling for deterministic `size_bytes`, and removes time-dependent stamping.
  - `regen_plan_checklist.py` now emits a stable banner string so outputs stop thrashing when the date changes.
- **Branch protection JSON parse error (HTTP 400)** → fixed by writing JSON as UTF-8 **without BOM** before calling `gh api -X PUT .../protection`.
- **PowerShell quoting/piping friction for `gh run list`** → documented safe patterns using `--json` + `--jq` (no external `jq` pipe).

## Still Open / Watchlist
- **Local path standardization**: decide whether to keep working in `C:\RichPanel_GIT` (recommended) or rename/migrate to `C:\RichPanel`.
- **External access prerequisites** (Build Mode): AWS account/roles, Richpanel API access, email provider, ShipStation/Marketplace keys.

## Notes
These are “meta” repo/ops issues; product requirement changes are tracked separately (e.g., CR-001).
