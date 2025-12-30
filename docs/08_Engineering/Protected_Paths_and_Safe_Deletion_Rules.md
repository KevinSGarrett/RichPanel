# Protected Paths and Safe Deletion Rules

Last updated: 2025-12-29  
Status: Canonical

This document defines which files/folders are protected from deletion/rename during routine development.

Protected paths exist to prevent “cleanup” or refactors from accidentally removing:
- the documentation system
- the rehydration pack
- policies/templates
- CI/workflow infrastructure

---

## Protected paths (must not delete/rename without PM approval)

- `docs/`
- `REHYDRATION_PACK/`
- `PM_REHYDRATION_PACK/`
- `policies/`
- `reference/`
- `.github/`
- `scripts/`
- `config/`
- root files: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`

---

## When deletions are allowed
Deletions/renames inside protected paths require:

1) explicit PM approval (written)
2) recording the approval in:
   - `REHYDRATION_PACK/DELETE_APPROVALS.yaml`
3) updating:
   - `docs/CODEMAP.md`
   - `docs/REGISTRY.md` (regen)
   - any impacted indexes

---

## Automated guardrails
- `python scripts/check_protected_deletes.py` (fails on protected deletes unless approved)

This script is intended to run both locally and in CI.
