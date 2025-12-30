# Docs Impact Map — Wave 12 Update 2

Date: 2025-12-23

This update adds “execution-layer” planning aids that sit on top of the existing Wave 12 ticket packs.

## Primary new docs
- Sprint plan: `docs/12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md`
- V1 cutline: `docs/12_Cursor_Agent_Work_Packages/00_Overview/V1_Cutline_and_Backlog.md`
- Jira import: `docs/12_Cursor_Agent_Work_Packages/00_Overview/Jira_Import_Instructions.md`

## Cross-wave alignment
- Sprint plan aligns to:
  - **Wave 06:** kill switch + security baseline requirements
  - **Wave 07:** concurrency/backpressure + degraded mode expectations
  - **Wave 08:** observability event taxonomy + dashboards
  - **Wave 09:** smoke tests + staged rollout and go/no-go gates
  - **Wave 10:** runbooks + mitigation levers
  - **Wave 11:** governance cadence (post-launch loop)

## Build tracking alignment
- Ticket metadata in `assets/tickets_v1.csv` now includes:
  - `story_points`, `priority`, `scope`, `sprint`, `component`, `suggested_role`
- Sprint mapping is also exported in `assets/sprint_plan_v1.csv`.
- Jira imports are provided in two files (epics then tasks).

## Risk and scope
- **POST_V1** default: Shopify fallback (`W12-EP05-T052`) to avoid prematurely expanding scope.
- Optional hardening inside existing tickets:
  - WAF portion of `W12-EP08-T083` (throttling remains required).
