# Execution Pack Overview (Wave 12)

Last updated: 2025-12-23 (Update 2)

This wave converts the documentation plan into **implementation-ready work packages** your builders can execute with Cursor agents.

These execution packs are designed for your workflow:
1. ChatGPT = project documentation plan manager (this repo's docs are the source of truth)
2. Cursor agents = builders who implement tickets and return a summary + updated project folder ZIP

---

## What these packs include
- A **work breakdown structure** (epics → tickets) aligned to the plan docs.
- **Ticket-by-ticket acceptance criteria**, including security and testing gates.
- Dependencies and recommended sequencing for the fastest safe rollout.
- Copy/paste **Cursor run prompts** and expected outputs.

---

## Definitions
### “Route-only mode”
The middleware applies routing tags/assignment **without sending customer auto-replies**.

### “Safe mode”
A runtime state where automation is disabled (or heavily restricted) while ingestion and routing continue.
See: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`.

### “Deterministic match”
A Tier 2 automation may disclose order-specific info only when a verified order link exists
(e.g., Richpanel order linkage endpoint returns an order) and policy gates pass.

---

## Builder deliverables (standard)
Each ticket should produce:
1. **Implementation** (code/IaC/config) as described
2. **Tests** as required (unit/integration/smoke)
3. **Documentation updates** (only if implementation changes the plan assumptions)
4. A **Cursor summary** covering:
   - what changed
   - how to run/test
   - risks / follow-ups
   - any deviations from ticket plan (with rationale)

---

## How to use these packs
These packs can be used in two ways:
- **Sprint plan:** use `00_Overview/Implementation_Sequence_Sprints.md` (recommended).
- **Cutline-first:** build all **P0 v1** tickets first using `00_Overview/V1_Cutline_and_Backlog.md`.

Recommended build sequence (high level):
1. Sprint 0–1: EP00 (preflight) + EP01/EP02 (AWS + IaC/CI foundations)
2. Sprint 2: EP03 (middleware core pipeline)
3. Sprint 3: EP04 + EP06 + EP07 (Richpanel integration + LLM routing + templates) — **route-only first**
4. Sprint 4: EP05 + EP07 + EP08 (order status + automation + security/observability baseline)
5. Sprint 5: EP09 (testing + staged rollout)

If you want to mirror this work in Jira, see `00_Overview/Jira_Import_Instructions.md`.

This order matches the progressive enablement strategy in:
- `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`
- `docs/09_Deployment_Operations/Release_and_Rollback.md`

---

## Notes on deferred Richpanel tenant verification
Some tenant capabilities were deferred (Wave 03). These packs treat them as:
- **non-blocking** for most implementation (safe defaults exist)
- **required** to finalize webhook auth and automation triggers before go-live

See: EP00 and the deferred list in `docs/ROADMAP.md`.
