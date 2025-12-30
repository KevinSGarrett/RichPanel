# Agent Assignments (Next Run Set)

We run **3 Cursor agents** in parallel when possible.

**Current target wave:** Wave 02 (Reference indexing) + Wave 03 (Pack automation prep)

**Run ID convention:** `RUN_<YYYYMMDD>_<HHMMZ>` (UTC)

---

## Agent A — Infra scaffold hardening (CDK)
**Objective**
- Initialize `infra/cdk/` as a valid CDK app (TypeScript) that can synth/deploy a minimal stack.

**Deliverables**
- `infra/cdk/` scaffold (cdk.json, package.json, bin/, lib/)
- `infra/README.md` updated with chosen tool + how to run
- Minimal “no-op” stack that deploys (even if resources are placeholders)
- Run outputs in `REHYDRATION_PACK/RUNS/<RUN_ID>/A/`

**Key references**
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- `docs/12_Cursor_Agent_Work_Packages/03_Tickets/W12-EP02-T020_Select_IaC_tool_and_scaffold_infrastructure_repo_modules_serverless_stack.md`

---

## Agent B — Richpanel reference library indexing (Wave 02)
**Objective**
- Make `reference/richpanel/` searchable and “index-first”.

**Deliverables**
- `reference/richpanel/INDEX.md` (curated)
- `reference/richpanel/_generated/reference_registry.json` (path + title guess + tags)
- “Top 20” list for most-used docs
- Run outputs in `REHYDRATION_PACK/RUNS/<RUN_ID>/B/`

**Key references**
- `reference/richpanel/Non_Indexed_Library/` (raw)
- `docs/03_Richpanel_Integration/` (what we actually need from vendor docs)

---

## Agent C — Rehydration pack automation + templates refresh (Wave 03 prep)
**Objective**
- Enforce rehydration pack validity and improve templates for A/B/C.

**Deliverables**
- `scripts/verify_rehydration_pack.py` (required files, size checks, run folder structure)
- Update `REHYDRATION_PACK/_TEMPLATES/` to use Agent A/B/C and new run ID convention
- Update `docs/98_Agent_Ops/Rehydration_Pack_Spec.md` if needed
- Run outputs in `REHYDRATION_PACK/RUNS/<RUN_ID>/C/`

---

PM: split the next wave into these three prompts and require each agent to update docs directly.
