# Issue Log

Last verified: 2025-12-29 — Wave F05 (issue tracking scaffolded).

This is the **canonical index** of issues found during development/build.

## Why this exists
AI agents need a persistent memory of:
- what broke
- where it broke
- how it was fixed
- what tests proved the fix

To keep token usage low, each issue is stored as its own file under `Issues/`,
and this file remains a navigable index.

## Issue ID convention
- `ISSUE-YYYYMMDD-###` (e.g., `ISSUE-20251229-001`)

## Index

| Issue ID | Status | Area | Summary | Affected files | Fix PR/Commit | Evidence |
|---|---|---|---|---|---|---|
| (none yet) |  |  |  |  |  |  |

## Add a new issue
1. Copy: `docs/00_Project_Admin/Issues/ISSUE_TEMPLATE.md`
2. Save as: `docs/00_Project_Admin/Issues/<ISSUE-ID>__Short_Title.md`
3. Add a row to the table above
4. Update `CHANGELOG.md` if the fix was meaningful
