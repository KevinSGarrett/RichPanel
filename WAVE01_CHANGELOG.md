# Wave 01 Foundation Update — Changelog

Date: 2025-12-23

This update locks key decisions and hardens PM/agent conventions for implementation.

## Decisions locked
- IaC tool of record: **AWS CDK (TypeScript)** (`infra/cdk/`)
- Runtime architecture: **AWS serverless** (API GW → Lambda ingress → SQS FIFO → workers → DynamoDB)
- Secrets manager: **AWS Secrets Manager**
- Frontend: **planned** (skeleton placeholder under `frontend/`)
- Agents: **A/B/C**, docs-updates allowed every run, refactors allowed with guardrails

## New / updated paths
- NEW: `PM_REHYDRATION_PACK/` (PM self-hydration for this chat/task)
- UPDATED: `REHYDRATION_PACK/` conventions:
  - run id format: `RUN_<YYYYMMDD>_<HHMMZ>`
  - per-agent folders: `RUNS/<RUN_ID>/{A,B,C}/...`
  - templates updated accordingly
- NEW: `docs/98_Agent_Ops/Policies/POL-OVR-001__Project_Overrides_(Agent_Rules).md`
- NEW: `docs/98_Agent_Ops/Agent_Roles_and_Concurrency.md`
- NEW: `infra/cdk/` scaffold (CDK TypeScript app skeleton)
- NEW: `frontend/` placeholder skeleton
- NEW: `scripts/verify_rehydration_pack.py`
- UPDATED: `docs/CODEMAP.md`, root `README.md`, `scripts/README.md`
- Regenerated: `docs/REGISTRY.md` and `docs/_generated/doc_registry.json`

## Next wave focus
- Wave 02: index `reference/richpanel/`
- Wave 03: pack automation + validation improvements
