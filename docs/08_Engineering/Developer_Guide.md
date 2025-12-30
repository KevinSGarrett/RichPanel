# Developer Guide

Last verified: 2025-12-29 — Wave F05 (developer guide scaffolded).

This is the canonical guide for developers/agents working in this repo.
Keep it concise and link to deeper docs.

## Repo orientation (read in order)
1. `docs/INDEX.md` — main documentation index
2. `docs/CODEMAP.md` — where code and docs live
3. `docs/02_System_Architecture/System_Overview.md` — what we’re building
4. `docs/98_Agent_Ops/AI_Worker_Retrieval_Workflow.md` — how to find info efficiently

## Local prerequisites
- Python 3.11+
- Node.js (for CDK and planned Next.js admin console)
- AWS credentials configured (for synth/deploy when build begins)

## Common commands (foundation mode)
These commands validate documentation and rehydration pack structure.

```bash
python scripts/verify_rehydration_pack.py
python scripts/regen_doc_registry.py
python scripts/regen_reference_registry.py
python scripts/verify_plan_sync.py
```

## When build starts (build mode)
- Backend code will live under: `backend/src/`
- Infra will live under: `infra/cdk/`
- Frontend will live under: `frontend/admin/`

## Documentation update expectations (agents)
See: `docs/98_Agent_Ops/Living_Documentation_Set.md`

## Testing expectations
See:
- `docs/08_Testing_Quality/Test_Strategy_and_Matrix.md`
- `docs/08_Testing_Quality/Test_Evidence_Log.md`

## Troubleshooting
- If a verifier fails, read the error and fix the exact missing file/link.
- If docs drift, update:
  - `docs/INDEX.md`
  - `docs/REGISTRY.md` (regenerated)
  - `docs/_generated/*` (regenerated)
