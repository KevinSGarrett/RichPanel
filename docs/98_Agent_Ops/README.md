# Agent Ops (Policies, Templates, and Run Protocols)

Last verified: 2025-12-29 — Wave F06.

This section is **for AI workers** (Cursor agents) and the **ChatGPT PM**.

It contains:
- canonical agent policies (imported from `Policies.zip`)
- **project-specific overrides** (explicitly approved behavior tweaks)
- templates the agents must fill out each build run (Structure Report, Docs Impact Map, Fix Report, Test Matrix)
- standards for chunking/indexing and placeholder usage
- the Rehydration Pack spec (what must be kept up-to-date so the PM can re-hydrate quickly)

## Agents
We use **3 Cursor agents**:
- **Agent A**
- **Agent B**
- **Agent C**

## Read order (minimal tokens)
1. `Living_Documentation_Set.md` (what must stay continuously updated)
2. `Policies/POL-OVR-001__Project_Overrides_(Agent_Rules).md`
3. `Policies/` (especially `POL-STRUCT-001`, `POL-DOCS-001`, `POL-LIVE-001`, `POL-TEST-001`, `POL-GH-001`)
4. `Placeholder_and_Draft_Standards.md`
5. `Chunking_and_Indexing_Standard.md`
6. `Rehydration_Pack_Spec.md`
7. `Validation_and_Automation.md`
8. `Templates/`

## Scope
This folder governs **how we work**.

Product/system specs live in the main doc sections (`docs/01_Product_Scope_Requirements/` through `docs/12_Cursor_Agent_Work_Packages/`).

