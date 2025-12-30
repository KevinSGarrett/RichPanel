# File/Code/Folder Layout Policy

**Doc ID:** POL-STRUCT-001  
**Source:** `Policies.zip` (extended in Wave F05)  
**Last verified:** 2025-12-29  

## Goal
Maintain a clean, predictable repository layout that is easy to navigate with minimal searching and minimal token waste.

## Structural invariants (must always be true)
- Every new file has an intended “home” (folder) based on responsibility.
- Every major folder has an `INDEX.md` or `README.md` that explains what belongs there.
- New docs are linked from `docs/INDEX.md` and appear in the doc registry.

## Canonical top-level folders
- `docs/` — canonical project documentation (indexed + chunked)
- `REHYDRATION_PACK/` — token-efficient “current state” pack for PM
- `reference/` — vendor/reference docs (indexed; do not rewrite unless necessary)
- `backend/` — middleware runtime code (Python 3.11 planned)
- `infra/` — AWS infrastructure (CDK TypeScript)
- `frontend/` — admin console (Next.js TS planned)
- `config/` — **non-secret** configuration templates (e.g., `.env.example`)
- `qa/` — test evidence artifacts and QA helpers

## Search-minimization rule (“index-first navigation”)
Before broad searching:
1. Consult `docs/CODEMAP.md` + `docs/INDEX.md`
2. Consult folder-level `README.md` / `INDEX.md`
3. If searching is required, search within the most likely module folder first

If you had to search widely:
- Improve `docs/CODEMAP.md` so the next run is faster.

## Living documentation must stay accurate
If you change system structure:
- Update `docs/02_System_Architecture/System_Matrix.md`
- Update `docs/98_Agent_Ops/Living_Documentation_Set.md` (if new living docs are introduced)
