# CODEMAP (Docs Navigation)

Last updated: 2025-12-22

This repository folder is **primarily documentation** (project development plan).  
It may contain optional, non-production reference artifacts under `reference_artifacts/` to validate the plan.

Use:
- `docs/INDEX.md` for curated navigation
- `docs/REGISTRY.md` for a complete list of all docs (no orphan files)

---

## Top-level
- `README.md` — high-level overview and how to navigate
- `docs/INDEX.md` — master index of plan documents
- `docs/00_Project_Admin/Progress_Wave_Schedule.md` — roadmap and progress tracking (always updated)
- `docs/Waves/` — wave folders with wave-specific notes and checklists

---

## Major sections
- `docs/01_Product_Scope_Requirements/` — scope, requirements, workflows, departments, FAQs
- `docs/02_System_Architecture/` — architecture, hosting, data flow, diagrams
- `docs/03_Richpanel_Integration/` — webhook/event ingestion, API usage, tags/teams mapping
- `docs/04_LLM_Design_Evaluation/` — taxonomy, prompts, structured outputs, safety gates, eval plan
- `docs/05_FAQ_Automation/` — template copy, order status automation, playbooks, macro governance
- `docs/06_Security_Privacy_Compliance/` — PII policy, retention, webhook security, secrets/IAM, monitoring/alarms baseline, rotation runbooks, break-glass, incident response
- `docs/07_Reliability_Scaling/` — SLOs, capacity, backpressure, costs, recovery
- `docs/08_Testing_Quality/` — CI eval gates, QA plans, testing strategy
- `docs/09_Deployment_Operations/` — release/rollback, environments, operations
- `docs/10_Governance_Continuous_Improvement/` — drift/calibration, change management
- `docs/11_Cursor_Agent_Work_Packages/` — build-ready ticket packs aligned with `Policies.zip`
- `docs/90_Risks_Common_Issues/` — risk mapping, common issues mitigation, FMEA/threat model tie-ins

---

## Structural invariants (project policies)
- No orphan docs: every substantive file must be linked from `docs/REGISTRY.md`.
- Update `docs/INDEX.md` and this CODEMAP whenever structure changes.
- Prefer modular docs over “god files”.
