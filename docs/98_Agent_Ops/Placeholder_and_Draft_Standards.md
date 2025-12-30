# Placeholder and Draft Standards

Last verified: 2025-12-29 — Wave F06.

This repo intentionally uses placeholders during early waves. However, ambiguous placeholders cause AI drift.
This document defines what is allowed and what is not.

---

## Allowed placeholder forms (preferred)

Use explicit markers so an AI agent understands this is unfinished:

- `TODO:` — work required (include owner or wave if possible)
- `TBD:` — decision required (include where the decision will be recorded)
- `<<PLACEHOLDER: ... >>` — intentionally blank scaffold (include intended content type)

Example:

```md
## API authentication

TBD: Confirm whether Richpanel HTTP targets support custom headers. Record decision in:
- docs/00_Project_Admin/Decision_Log.md
```

---

## Disallowed placeholders in canonical docs

Avoid these in docs linked from `docs/INDEX.md`:

- A naked `...` or `…` (ambiguous: is it truncation, missing content, or a formatting artifact?)
- Vague text like “fill in later” without telling the agent **where** and **how** to fill it

---

## How to handle legacy/plan artifacts

Some plan artifacts may contain incomplete sections.
Do not “silently” edit history-heavy plan artifacts.
Instead:
1) add a short note in the canonical doc that supersedes the legacy text
2) link back to the legacy artifact for context
3) if needed, capture the delta in `CHANGELOG.md`

---

## Hygiene checks

Use:
- `python scripts/verify_doc_hygiene.py` (warnings by default; `--strict` fails)

