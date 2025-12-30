# Richpanel Middleware (Plan + Implementation)

Last updated: 2025-12-28 (Wave 01b)

This repo contains:
1) The **end-to-end, production-grade project plan** (under `docs/`)
2) The **implementation scaffold** (under `backend/`, `infra/`, `qa/`, `frontend/`)
3) The **AI operations system** (under `REHYDRATION_PACK/`) used to coordinate ChatGPT PM + Cursor agents
4) The **PM self-hydration pack** (under `PM_REHYDRATION_PACK/`) used to prevent drift while building the repo OS in this chat

---

## What we’re building (North Star)
We are building a middleware that:

1) Routes inbound Richpanel customer messages to the correct department/team using an LLM + confidence scoring  
2) Safely automates top FAQs (starting with order status & tracking)  
3) Falls back to humans when confidence is low, content is ambiguous, or required data is missing  
4) Applies defense-in-depth: idempotency, rate limits, PII handling, prompt-injection controls, and kill switches

See: `REHYDRATION_PACK/01_NORTH_STAR.md`

---

## Where to start reading (minimal)
1) `REHYDRATION_PACK/00_START_HERE.md`
2) `docs/INDEX.md`
3) `docs/CODEMAP.md`

---


## Tech stack defaults (locked)
- **Infra/IaC:** AWS CDK (TypeScript) — `infra/cdk/`
- **Backend (Lambda runtime):** Python 3.11 — `backend/`
- **Admin UI (planned):** Next.js (TypeScript) — `frontend/admin/` (implementation later)
- **Secrets:** AWS Secrets Manager

## Repo navigation
- `docs/CODEMAP.md` — where everything lives
- `docs/ROADMAP.md` — module roadmap + streams
- `docs/REGISTRY.md` — full list of docs
- `docs/98_Agent_Ops/` — agent policies + templates + run protocols

---

## Reference docs
Raw Richpanel reference materials live under `reference/richpanel/`.

---

## Infra
Primary IaC tool (v1): **AWS CDK (TypeScript)** → `infra/cdk/`.