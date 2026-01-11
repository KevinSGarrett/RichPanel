# Task Board (Prioritized)

> This is the **single most important** file for "what to do next".

Last updated: 2026-01-10 (Run reporting + prompt archive + checklist hygiene)

**Current mode:** build (implementation active).  
Environment state (dev/staging/prod) is **not asserted** here unless explicitly linked to evidence. Prod promotion remains gated.

---

## Progress dashboard (repo-shipped vs roadmap)

Status definitions:
- **Shipped**: merged into the repo (code/docs/workflows exist)
- **In progress**: actively being implemented in the repo
- **Roadmap**: planned/pending (not shipped yet)

Based on `docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md` (CHK-001..017):
- Total epics: 17
- Shipped: 9 (52.9%)
- In progress: 2 (11.8%)
- Roadmap: 6 (35.3%)

## P0 — Integrations + configuration (do next)
- [ ] Shopify integration: confirm credentials + data availability + fallback behavior
- [ ] ShipStation integration (if used): confirm credentials + field mapping
- [ ] Shopify/ShipStation order lookup implementation (gated enrichment + tests) - in progress
- [ ] Richpanel UI configuration: document required settings and validation steps
- [ ] Confirm order-status semantics and CR-001 behavior in real Richpanel flows (staging first)

## Roadmap / next (P0) - Release gates (keep green)
Goal: stay safe while shipping.

- [ ] Keep safety defaults intact (safe_mode + automation_enabled + dry-run)
- [ ] Maintain doc anti-drift gate (`verify_admin_logs_sync`)
- [ ] Keep smoke evidence recorded (links in test evidence log)
- [ ] Prod remains gated until explicit human go/no-go + evidence capture

## Midpoint Audit (WaveAudit)
- Checklist: `docs/00_Project_Admin/To_Do/MIDPOINT_AUDIT_CHECKLIST.md`
- Rule: treat each checkbox as ???not done??? until evidence is captured (commands + outputs + links/screenshots as applicable).


---

## Done (Shipped in repo)

- DONE: TASK-251 - Bugbot PR loop documented (trigger via `@cursor review` / `bugbot run`) (Runbook)
- DONE: TASK-250 - Offline-first integration skeletons present (Richpanel/OpenAI/Shopify/ShipStation) (skeletons)
- DONE: TASK-240 - Added PM prompts, RUN scaffolding script, and GitHub ops policy (Wave F10)

- DONE: TASK-230 - Clarified Foundation vs Build and mapped legacy Wave 00-10 schedule (Wave F10)

- DONE: TASK-210 - Resolved doc hygiene warnings in INDEX-linked docs (Wave F07)

- DONE: TASK-160 - Foundation readiness review scaffolding + activation checklist doc added (Wave F06)
- DONE: TASK-161 - Plan -> checklist extraction added (generated view + JSON) (Wave F06)
- DONE: TASK-162 - Legacy redirect folders standardized (MOVED.md stubs) (Wave F06)
- DONE: TASK-150 - Policy library hardening (Living Docs rules added) (Wave F05)
- DONE: TASK-151 - Template hardening (added templates for changelog/decision/test evidence/docs checklist/config changes) (Wave F05)
- DONE: TASK-152 - Added living documentation set + pointers (Wave F05)
- DONE: TASK-001 - Locked core stack decisions (CDK, serverless, Secrets Manager, frontend planned)
- DONE: TASK-003 - Added mode flag + clarified foundation vs build workflow
- DONE: TASK-100-122 - Docs indexing + navigation hardening (machine registries; wave schedule; navigation)
- DONE: TASK-130 - Mode-aware rehydration pack validation (MANIFEST v2 + verify script)
- DONE: TASK-140-143 - Reference indexing
