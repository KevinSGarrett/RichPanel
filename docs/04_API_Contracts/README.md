# API Contracts

Last verified: 2025-12-29 — Wave F05.

This folder contains the **canonical API surface definitions** for *our system* (not vendor docs).

## What belongs here
- **Ingress endpoints** (e.g., Richpanel webhook receiver)
- **Health checks**
- **Admin API** (if/when added)
- **Internal event schemas** (if they’re used across components)

## Primary files
- `API_Reference.md` — human-readable overview of endpoints + behaviors
- `openapi.yaml` — OpenAPI source of truth (keep minimal and accurate)

## Related
- Richpanel integration details: `docs/03_Richpanel_Integration/`
- Vendor docs: `reference/richpanel/`
