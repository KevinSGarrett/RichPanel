# Task Board (Prioritized)

> This is the **single most important** file for “what to do next”.

Last updated: 2025-12-29 (Wave F12)

**Current mode:** foundation (structure + docs).  
Cursor prompts/summaries/run outputs are **not required** until we switch to build mode.

---

## P0 — CR-001 no-tracking delivery estimates (pre-build)
- [ ] Confirm Shopify/Richpanel shipping method strings -> Standard/Rushed/Priority/Pre-Order mapping
- [ ] Confirm business-day calendar (Mon–Fri only vs holiday-aware)
- [ ] Confirm pre-order ETA source-of-truth (field/tag/metafield/policy table)
- [ ] Confirm Richpanel status semantics: "Resolved" and reopen-on-reply behavior
- [ ] Approve customer-facing copy for `t_order_eta_no_tracking_verified`

## P0 (do next) — Build-mode readiness finalization (no implementation yet)

Goal: ensure GitHub + CI + rehydration workflow are aligned so Cursor agents can operate end-to-end without manual intervention.

- **TASK-230:** Configure `main` protection + merge settings (required before build mode)
  - Follow: `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
  - Confirm required status check name: `CI / validate`
- **TASK-231:** Confirm `gh` is installed + authenticated in the Cursor environment
  - `gh auth status`
- **TASK-232:** Confirm CI-equivalent checks pass locally
  - `python scripts/run_ci_checks.py`
- **TASK-233:** Confirm build-mode activation checklist is satisfied
  - `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`

## P1 (optional, later) — Build-mode activation (implementation begins)

Goal: prepare to switch `REHYDRATION_PACK/MODE.yaml` from `foundation` → `build`.

Only do this when you are ready to start actual implementation.

- **TASK-200:** Review `FOUNDATION_STATUS.md` and confirm readiness gaps
- **TASK-201:** Complete `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- **TASK-202:** Flip mode to `build` in `REHYDRATION_PACK/MODE.yaml`
- **TASK-203:** Start **B00** (Build kickoff) and begin per-run artifact capture under `REHYDRATION_PACK/RUNS/`

---

## Done (Foundation)

- ✅ **TASK-240:** Added PM prompts, RUN scaffolding script, and GitHub ops policy (Wave F10)

- ✅ **TASK-230:** Clarified Foundation vs Build and mapped legacy Wave 00–10 schedule (Wave F10)

- ✅ **TASK-210:** Resolved doc hygiene warnings in INDEX-linked docs (Wave F07)

- ✅ **TASK-160:** Foundation readiness review scaffolding + activation checklist doc added (Wave F06)
- ✅ **TASK-161:** Plan → checklist extraction added (generated view + JSON) (Wave F06)
- ✅ **TASK-162:** Legacy redirect folders standardized (MOVED.md stubs) (Wave F06)
- ✅ **TASK-150:** Policy library hardening (Living Docs rules added) (Wave F05)
- ✅ **TASK-151:** Template hardening (added templates for changelog/decision/test evidence/docs checklist/config changes) (Wave F05)
- ✅ **TASK-152:** Added living documentation set + pointers (Wave F05)
- ✅ **TASK-001:** Locked core stack decisions (CDK, serverless, Secrets Manager, frontend planned)
- ✅ **TASK-003:** Added mode flag + clarified foundation vs build workflow
- ✅ **TASK-100–122:** Docs indexing + navigation hardening (machine registries; wave schedule; navigation)
- ✅ **TASK-130:** Mode-aware rehydration pack validation (MANIFEST v2 + verify script)
- ✅ **TASK-140–143:** Reference indexing


---

## Next: Build mode activation (when you are ready to start implementation)
- [ ] Review `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- [ ] Ensure GitHub settings are configured for agent-driven PR merge (recommended)
- [ ] Flip `REHYDRATION_PACK/MODE.yaml` to `mode: build`
- [ ] Create first run folder: `python scripts/new_run_folder.py --now`
- [ ] Populate `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md`
- [ ] Populate `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` with Agent A/B/C prompts
