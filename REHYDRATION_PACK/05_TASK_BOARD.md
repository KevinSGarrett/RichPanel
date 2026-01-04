# Task Board (Prioritized)

> This is the **single most important** file for “what to do next”.

Last updated: 2026-01-03 (Wave B06)

**Current mode:** build (implementation active).  
Dev + staging are deployed and smoke tests are green; prod promotion is gated.

---

## P0 — Integrations + configuration (do next)
- [ ] Shopify integration: confirm credentials + data availability + fallback behavior
- [ ] ShipStation integration (if used): confirm credentials + field mapping
- [ ] Richpanel UI configuration: document required settings and validation steps
- [ ] Confirm order-status semantics and CR-001 behavior in real Richpanel flows (staging first)

## P0 — Release gates (keep green)
Goal: stay safe while shipping.

- [ ] Keep safety defaults intact (safe_mode + automation_enabled + dry-run)
- [ ] Maintain doc anti-drift gate (`verify_admin_logs_sync`)
- [ ] Keep dev/staging smoke evidence recorded (links in test evidence log)
- [ ] Prod remains gated until explicit human go/no-go + evidence capture

---

## Done (build baseline)

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

