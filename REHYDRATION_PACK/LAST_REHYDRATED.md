# Last Rehydrated

- Date: 2025-12-29
- Wave: Wave F12 — GitHub defaults locked + branch protection docs + protected delete guard improved
- Mode: foundation

Notes:
- GitHub decisions locked: main protected (PR required), merge commit, `gh` available, sequential default.
- `scripts/check_protected_deletes.py` now falls back gracefully when commit-range diffs are unavailable.
