# Environment & Config (Canonical)

Last verified: 2025-12-29 — Wave F05.

This doc defines **how configuration works**, what is safe to store, and where to update values.

## Source of truth
- Example template: `config/.env.example`
- Secrets: **AWS Secrets Manager** (never committed)

## When to update this doc
- Any new environment variable is introduced
- Any default value changes
- Any config key is renamed or removed

## Config categories
- **Runtime**: environment name, log level
- **Integrations**: Richpanel secrets, endpoints (if applicable)
- **LLM**: model selection (non-secret), prompt versions, gating thresholds
- **Safety**: kill switch, safe mode route-only, escalation toggles
- **Storage**: table names, bucket names (non-secret)

## Governance
If config changes are made, also update:
- `docs/02_System_Architecture/System_Matrix.md`
- `CHANGELOG.md`
- If change is security relevant: `docs/06_Security_Privacy_Compliance/`
