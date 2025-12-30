# Legacy Folder Redirects

Last verified: 2025-12-29 — Wave F06.

This file lists **legacy/redirect folders** that exist only to preserve older links.
They should contain **MOVED.md** (and optionally a small README) and no canonical content.

If you are editing content and you land in a legacy folder, **follow the redirect** and edit the canonical target instead.

---

## Redirect folders

### Privacy/observability legacy split
- Legacy: `docs/06_Data_Privacy_Observability/`
- Canonical:
  - Security & privacy: `docs/06_Security_Privacy_Compliance/`
  - Observability & analytics: `docs/08_Observability_Analytics/`

### Governance (older numbering)
- Legacy: `docs/10_Governance_Continuous_Improvement/`
- Canonical: `docs/11_Governance_Continuous_Improvement/`

### Cursor execution packs (older numbering)
- Legacy: `docs/11_Cursor_Agent_Work_Packages/`
- Canonical: `docs/12_Cursor_Agent_Work_Packages/`

---

## Maintenance rules

- Redirect folders should contain:
  - `MOVED.md` (required)
  - `README.md` (optional)
- Redirect folders should **not** contain:
  - canonical specs
  - checklists that are actively updated
  - run templates

If canonical content accidentally lands in a redirect folder:
1) migrate it to the canonical location
2) update `docs/INDEX.md` links if needed
3) regenerate registries

