# Richpanel Middleware Project Plan (Documentation)

Last updated: 2025-12-22

This folder contains the **end-to-end, production-grade project development plan** for building a middleware that:
1) **Routes inbound Richpanel customer messages** to the correct department using OpenAI models and a confidence scoring system.
2) **Auto-resolves top FAQs** (starting with order status) by replying back to the customer when confidence is high enough.
3) **Falls back safely** to human agents when confidence is low, content is ambiguous, or required data is missing.

## How we will work (waves)
We will build these documents in **waves** (see `docs/00_Project_Admin/Progress_Wave_Schedule.md`).
After each wave/update:
- This documentation folder is updated.
- You re-upload the updated zip.
- We proceed to the next wave.

## Where to start
- `docs/00_Project_Admin/Progress_Wave_Schedule.md` — master roadmap + progress tracking
- `docs/00_Project_Admin/Rehydration.md` — “everything we know so far” (context + constraints)
- `docs/INDEX.md` — clickable index of all plan documents

## Source inputs referenced
The plan references these input bundles you provided:
- `CommonIssues.zip` — known pitfalls + mitigation guidance
- `RichPanel_Docs_Instructions_Library_001.zip` — Richpanel docs + configs (not re-embedded here due to size)
- `Policies.zip` — PM + Cursor agent rules and workflow expectations
- `RoughDraft.zip` — early blueprint + dataset summaries + prompt schemas
- `Agent Activity Heatmap.csv` — inbound volume by hour (capacity planning)
- `SC_Data_ai_ready_package.zip` — AI-ready dataset of customer conversations + agent responses

See `docs/99_Appendices/Data_Inputs.md` for details.

## Latest focus (current wave)
Wave 03 is focused on **Richpanel integration design**, including:
- HTTP Target trigger ordering (must run before “skip subsequent rules” assignment rules)
- source verification via a shared secret header
- minimal payload strategy + post-fetching ticket context via API
- de-conflicting legacy assignment rules to avoid “routing fights”
