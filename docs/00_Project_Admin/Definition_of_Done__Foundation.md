# Definition of Done — Foundation (File/Folder Structure + Documentation OS)

Last updated: 2025-12-29 — Wave F09

This document defines when the **Foundation** work is complete.

Foundation means:
- The repo has an **AI-first folder structure**
- The documentation library is **fully indexed and chunkable**
- The **REHYDRATION_PACK** can reliably “rehydrate” the ChatGPT Project Manager
- Policies, templates, and validators are in place so Cursor agents can later build without drift

Non-goal:
- Implementing the production system (that begins in **Build** waves).

---

## Foundation is complete when all of these are true

### A) Repo structure is present (skeletons + canonical paths)
- [ ] Repo root includes core folders: `docs/`, `reference/`, `config/`, `scripts/`, `qa/`, `backend/`, `infra/`, `frontend/`, `artifacts/`, `runs/`
- [ ] Canonical vs legacy doc paths are clear:
  - `docs/00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md`
  - legacy folders contain redirect stubs only (no competing sources of truth)

### B) Documentation library is navigable + indexed
- [ ] Human navigation works:
  - `docs/INDEX.md`
  - `docs/CODEMAP.md`
- [ ] Machine navigation exists:
  - `docs/_generated/doc_registry.json`
  - `docs/_generated/heading_index.json`
  - `docs/REGISTRY.md`
- [ ] Reference library is indexed:
  - `reference/richpanel/INDEX.md`
  - `reference/_generated/reference_registry.json`

### C) REHYDRATION_PACK is complete and self-validating
- [ ] `REHYDRATION_PACK/` exists and contains required artifacts:
  - `00_START_HERE.md`
  - `MANIFEST.yaml` (v2)
  - `MODE.yaml` (set to `foundation` during foundation)
  - `WAVE_SCHEDULE.md` + `WAVE_SCHEDULE_FULL.md`
- [ ] `python scripts/verify_rehydration_pack.py` passes

### D) Plan → To‑Do extraction is working
- [ ] `python scripts/regen_plan_checklist.py` runs successfully
- [ ] Generated outputs exist:
  - `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`
  - `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`

### E) Policies + templates enforce non-drift behavior
- [ ] Living documentation set exists:
  - `docs/98_Agent_Ops/Living_Documentation_Set.md`
- [ ] Policies require documentation updates when changes are made:
  - `docs/98_Agent_Ops/Policies/`
- [ ] Templates exist for standardized updates:
  - `docs/98_Agent_Ops/Templates/`
  - `REHYDRATION_PACK/_TEMPLATES/`

### F) Hygiene + sync validators pass (no ambiguous placeholders; no registry drift)
Run these from repo root:

```bash
python scripts/verify_rehydration_pack.py
python scripts/verify_plan_sync.py
python scripts/verify_doc_hygiene.py
```

Foundation is considered “DONE” when all three commands pass.

---

## What happens next (optional)

When you are ready to start implementation using Cursor agents:
1) Complete `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
2) Flip `REHYDRATION_PACK/MODE.yaml` to `mode: build`
3) Start **Build wave B00** (build kickoff)

Important:
- **B00 is not required** to complete the Foundation work.
- B00 is only required when you decide to begin building the system.
