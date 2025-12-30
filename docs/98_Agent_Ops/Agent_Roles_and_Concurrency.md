# Agent Roles and Concurrency (A/B/C)

Last updated: 2025-12-23

This file defines how the **ChatGPT PM** and the **3 Cursor agents** collaborate without drifting.

---

## 1) Roles
### ChatGPT (PM)
- Owns: prioritization, scope control, decision locks, prompt writing, integration review.
- Must rehydrate every cycle from `REHYDRATION_PACK/00_START_HERE.md`.
- Must enforce: tests + docs + structure maps.

### Agent A (Builder)
- Default focus: backend + infra-heavy tickets (core pipeline, infra scaffolding).
- Owns: runnable scaffolds, entrypoints, interfaces, and keeping quality gates green.

### Agent B (Builder)
- Default focus: reference/docs indexing, Richpanel config mapping, template/macro alignment.
- Owns: making vendor + internal specs “index-first” and reducing search cost.

### Agent C (Builder)
- Default focus: QA/evals harness + tooling + pack automation.
- Owns: test layout, eval harness, CI/verification scripts, run report hygiene.

> The PM can reassign roles per wave, but should preserve a stable default to avoid thrash.

---

## 2) Concurrency model
Default: run A/B/C **in parallel** when tasks do not touch the same files.

If tasks may conflict, run in sequence:
1) Agent A (code/infra contracts)
2) Agent C (tests/verification scaffolding)
3) Agent B (docs/index updates)

---

## 3) Merge discipline (conflict avoidance)
- Each agent should work in a clearly scoped area.
- If an agent must touch a shared file (e.g., `docs/CODEMAP.md`):
  - do it at the end of the run
  - keep changes minimal
  - record the change in `STRUCTURE_REPORT.md`

---

## 4) Per-run required outputs
Each agent must write a run folder:
`REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/...` using the templates.

---

## 5) “Stop and ask PM” triggers (hard)
- Requirement ambiguity where behavior would be guessed
- Contract changes (schemas, APIs, DB shape) without PM approval
- Anything that could leak PII or secrets
- Any change that disables/weakens tests or security controls
