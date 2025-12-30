# CODEMAP (Project Navigation)

Last verified: 2025-12-29 — Wave F06.

This file explains **where things live** in the repo so an AI agent can navigate quickly and avoid drift.

---

## What this repository contains

1) **Project documentation** under `docs/`  
   The implementation plan + ongoing specs + living docs.

2) **AI operations** under `REHYDRATION_PACK/`  
   The “always attached” hydration bundle the ChatGPT PM reads each cycle.


3) **Repo automation and GitHub workflow**
- `.github/` — issue/PR templates (and later CI workflows)
- `scripts/` — validators + registry generators + run-folder scaffolding (`new_run_folder.py`)

3) **PM self-hydration (meta)** under `PM_REHYDRATION_PACK/`  
   Keeps this ChatGPT window aligned across many foundation waves.

4) **Implementation code** (scaffolds first, then real code)
   - `backend/` — runtime code (Python 3.11)
   - `infra/` — infrastructure as code (AWS CDK, TypeScript)
   - `frontend/` — planned admin UI (Next.js, TypeScript)
   - `qa/` — test harness + evidence artifacts
   - `scripts/` — verification + registry regeneration tooling

5) **Vendor/reference docs** under `reference/`  
   External documentation indexed for lookup.

---

## Primary “start here” entrypoints

- `REHYDRATION_PACK/00_START_HERE.md` — operational read order
- `docs/INDEX.md` — curated docs navigation
- `docs/REGISTRY.md` — complete docs list
- `docs/_generated/heading_index.json` — heading-level lookup (machine)
- `reference/INDEX.md` — curated vendor/reference navigation

---

## Docs sections (canonical plan)

Major sections:
- `docs/00_Project_Admin/` — decisions, progress, risks, checklists, governance admin docs
- `docs/01_Product_Scope_Requirements/` — scope, requirements, workflows, departments, FAQs
- `docs/02_System_Architecture/` — architecture, data flow, diagrams, system matrix
- `docs/03_Richpanel_Integration/` — webhook/event ingestion, API usage, tags/teams mapping
- `docs/04_LLM_Design_Evaluation/` — taxonomy, prompts, structured outputs, evals, safety gates
- `docs/05_FAQ_Automation/` — copy/templates, playbooks, macro governance
- `docs/06_Security_Privacy_Compliance/` — PII handling, retention, threat model, security controls
- `docs/07_Reliability_Scaling/` — SLOs, capacity, backpressure, recovery
- `docs/08_Observability_Analytics/` — event schemas, dashboards, drift detection
- `docs/09_Deployment_Operations/` — deployment runbooks, env config
- `docs/10_Operations_Runbooks_Training/` — ops handbook, training guides, runbook index
- `docs/11_Governance_Continuous_Improvement/` — governance program + change mgmt + versioning
- `docs/12_Cursor_Agent_Work_Packages/` — execution packs used during build mode
- `docs/98_Agent_Ops/` — policies, templates, standards

---

## Legacy / redirect folders

Redirect folders exist only to preserve older links. They contain `MOVED.md` stubs.
See:
- `docs/00_Project_Admin/Legacy_Folder_Redirects.md`

---

## Machine registries (generated)

Generated (do not hand-edit):
- Docs registry: `docs/_generated/doc_registry.json`
- Docs outline: `docs/_generated/doc_outline.json`
- Heading index: `docs/_generated/heading_index.json`
- Reference registry: `reference/_generated/reference_registry.json`

Regenerate:
- `python scripts/regen_doc_registry.py`
- `python scripts/regen_reference_registry.py`

---

## “Always-update” living docs

See the canonical list:
- `docs/98_Agent_Ops/Living_Documentation_Set.md`

Pointer map (token-efficient):
- `REHYDRATION_PACK/CORE_LIVING_DOCS.md`

