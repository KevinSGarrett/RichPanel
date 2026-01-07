# Repository Conventions

Last verified: 2025-12-29 — Wave F05.

This document captures conventions that agents must follow.

## File naming
- Markdown docs: `Title_With_Underscores.md`
- Templates: `*_TEMPLATE.md`
- Index files: `INDEX.md` at folder roots

## “Living docs” vs “Reference docs”
- Living docs are updated continuously as the system evolves.
- Reference docs (e.g., vendor library) are indexed and linked but not rewritten.

See: `docs/00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md`

## Diffs
- Prefer small, targeted changes.
- Avoid reformatting unrelated sections.

## Formatting
- `.editorconfig` at the repo root is the canonical source for charset/whitespace defaults.
- Use an EditorConfig-aware editor and avoid repo-wide reformatting outside intended scope.

## Source-of-truth rules
- API surface → `docs/04_API_Contracts/openapi.yaml`
- Decisions → `docs/00_Project_Admin/Decision_Log.md`
- Issues → `docs/00_Project_Admin/Issue_Log.md` + `docs/00_Project_Admin/Issues/`
- Security → `docs/06_Security_Privacy_Compliance/`
