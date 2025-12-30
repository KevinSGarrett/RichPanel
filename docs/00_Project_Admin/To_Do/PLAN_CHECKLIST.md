# PLAN CHECKLIST (Traceable to Plan Docs)

Last verified: 2025-12-29 — Wave F06.

This checklist is intended to be **traceable** back to the Automation Plan documentation in `docs/`.

## How this works (AI-first)

### Source of truth
The **source of truth** for atomic tasks remains in the individual plan docs as markdown checkboxes (`- [ ] ...`).

### Compiled view (generated)
We maintain an auto-generated compiled view for fast retrieval:

- Full extracted list (grouped by doc + heading):  
  `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`

- Machine-readable JSON (for agents/tools):  
  `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`

- Summary (counts by section):  
  `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_SUMMARY.md`

To regenerate:
```bash
python scripts/regen_plan_checklist.py
```

**Do not hand-edit the generated outputs.**  
Instead, update the checkboxes in the source doc(s) and regenerate.

---

## How to use during build

When an agent completes work:
1) Update the relevant source doc checklist items (check the boxes)
2) Add test evidence in:
   - `docs/08_Testing_Quality/Test_Evidence_Log.md`
   - `qa/test_evidence/`
3) Update living docs as required (see `docs/98_Agent_Ops/Living_Documentation_Set.md`)
4) Update `CHANGELOG.md`

---

## Recommended tracking workflow

- Use `MASTER_CHECKLIST.md` for epics/milestones (stays short)
- Use this file + the extracted list for atomic plan items
- Use `BACKLOG.md` for unscheduled ideas
- Use `DONE_LOG.md` for major completions

