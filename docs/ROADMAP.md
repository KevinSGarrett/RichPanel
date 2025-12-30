# Roadmap (High-Level)

Last verified: 2025-12-29 — Wave F06.

This is a high-level roadmap for both:
- **Foundation** (documentation OS)
- **Build** (implementation)

For the authoritative wave plan, see:
- `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md`

---

## Phase F — Foundation (mode: foundation)

- F00–F04: structure, indexing, vendor reference indexing ✅ Done
- F05: policy + template hardening; living docs set ✅ Done
- **F06: foundation readiness + plan→checklist extraction ✅ Done**

---

## Phase B — Build (mode: build)

Build mode begins after the activation checklist is satisfied:
- `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`

Planned build waves (subject to change; see full schedule):
- B00: ingest/ACK-fast + queueing baseline
- B01: router MVP (intent → dept) + confidence gates
- B02: automation MVP (FAQ + order status) + safety policy
- B03: observability/audit trail baseline
- B04: security controls + compliance readiness
- B05: staging/prod deploy + ops runbooks hardening
- B06+: evals, tuning, and continuous improvement

---

## Next step (switch to build mode)

1) Review and complete any remaining activation items:
   - `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
2) Change `REHYDRATION_PACK/MODE.yaml` to:
   - `mode: build`
3) Start using:
   - `docs/12_Cursor_Agent_Work_Packages/` (epics → tickets → prompts)
   - `REHYDRATION_PACK/RUNS/<RUN_ID>/` (per-run artifacts)

