# Jira Import Instructions — Wave 12

Last updated: 2025-12-23

These instructions help you import the **Wave 12 execution packs** into Jira as:
- **Epics** (EP00–EP09)
- **Tasks** (49 implementation tickets)

> Why two files?
> Jira typically requires **Epic keys** to link tasks to epics. We provide:
> - an epic CSV (create epics first)
> - a story/task CSV (then fill the epic keys and import tasks)

---

## Files

All files live under:

- `docs/12_Cursor_Agent_Work_Packages/assets/jira_epics_import_v1.csv`
- `docs/12_Cursor_Agent_Work_Packages/assets/jira_stories_import_v1.csv`

Optional planning aids:
- `assets/sprint_plan_v1.csv`
- `assets/epic_points_v1.csv`

---

## Step-by-step

### Step 1 — Import epics
1. Go to **Jira → External System Import → CSV**
2. Upload `jira_epics_import_v1.csv`
3. Map fields:
   - **Issue Type** → Issue Type
   - **Summary** → Summary
   - **Epic Name** → Epic Name
   - **Description** → Description
   - **Labels** → Labels
4. Import.

Result: Jira creates EP00–EP09 epics and assigns them real Jira keys (e.g., `MW-12`, `MW-13`).

### Step 2 — Prepare task import
1. Export or copy the epic keys created in Step 1.
2. Open `jira_stories_import_v1.csv`
3. Replace each placeholder in the `Epic Link` column:
   - `<FILL_EP00_KEY>` → the Jira key for EP00
   - `<FILL_EP01_KEY>` → the Jira key for EP01
   - Repeat for EP02–EP09.
4. Save the CSV.

### Step 3 — Import tasks
1. Upload the updated `jira_stories_import_v1.csv`
2. Map fields:
   - **Issue Type** → Issue Type
   - **Summary** → Summary
   - **Description** → Description
   - **Epic Link** → Epic Link
   - **Story Points** → Story Points (ensure your Jira has this field enabled)
   - **Priority** → Priority (optional)
   - **Labels** → Labels
   - **Component/s** → Component/s (optional)
   - **Assignee** → Assignee (optional — requires users to exist in Jira; otherwise leave unmapped)
3. Import.

---

## Notes and best practices

- **Descriptions include a link path** to the ticket markdown file in this repo, so engineers always have acceptance criteria + plan references.
- “Assignee” in the CSV is a **role hint** (Backend/Infra/Security/Ops). If Jira doesn’t recognize it, skip mapping.
- Use `assets/sprint_plan_v1.csv` as the base to create Jira sprints, then drag tickets into the right sprint.
- The **source of truth** remains the plan docs under `docs/`. Jira is a tracking mirror.

---

## Suggested Jira configuration (optional)
- Create labels:
  - `wave12`
  - `ep00` through `ep09`
- Create components:
  - `Infra`, `Middleware`, `Richpanel`, `LLM`, `Automation`, `SecurityObs`, `QARelease`
