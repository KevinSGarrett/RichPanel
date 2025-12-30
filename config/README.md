# Configuration & Environment

Last verified: 2025-12-29 — Wave F05.

This folder stores **non-secret** configuration templates and environment documentation.

## Rules
- **No secrets in repo.** Secrets live in AWS Secrets Manager.
- Keep `config/.env.example` updated when new env vars are introduced.
- If you add a new config value, also update:
  - `docs/09_Deployment_Operations/Environment_Config.md`
  - `docs/02_System_Architecture/System_Matrix.md`
  - `CHANGELOG.md`

## Files
- `.env.example` — example local env var template (NO secrets)
