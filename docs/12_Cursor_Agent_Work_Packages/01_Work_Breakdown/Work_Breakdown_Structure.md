# Work Breakdown Structure (Epics → Tickets)

Last updated: 2025-12-23

This WBS mirrors the documentation plan waves and converts them into implementation epics.

> **Principle:** Build in the same order you plan to roll out:
> ingestion + routing first, then controlled automation, then broader enablement.

---

## Epic list

### EP00 — Preflight access + tenant verification (non-blocking but required before go-live)
**Goal:** Confirm Richpanel tenant capabilities, ensure required access (API keys, Shopify tokens), and lock webhook auth method.
**Primary outputs:**
- Verified webhook trigger mechanism
- Verified HTTP Target auth capability (headers vs body token)
- Verified order linkage/tracking field availability via Richpanel APIs

### EP01 — AWS foundation (multi-account optional; minimum baseline required)
**Goal:** Create secure AWS environments (dev/stage/prod or minimal fallback) and baseline guardrails.
**Primary outputs:** accounts, budgets, logging baseline, IAM roles, secrets approach.

### EP02 — Infrastructure as Code + CI/CD foundation
**Goal:** Create repeatable deployments and safe release gating for prompts/templates/schemas.
**Primary outputs:** IaC modules, pipelines, promotion flow, environment config.

### EP03 — Middleware core pipeline (ingress → queue → worker → state)
**Goal:** Implement the serverless pipeline with idempotency, dedup, and safe fallback behavior.
**Primary outputs:** API Gateway, Lambdas, SQS FIFO + DLQ, DynamoDB idempotency/state, parameter flags.

### EP04 — Richpanel integration (tenant config + API client + action executor)
**Goal:** Route tickets and post replies safely using Richpanel APIs and tenant automations.
**Primary outputs:** team/tag setup, webhook config, Richpanel client, action executor.

### EP05 — Order status data path (Richpanel + Shopify fallback)
**Goal:** Provide deterministic order lookups and safe customer-facing tracking replies.
**Primary outputs:** order link lookup, order details fetch, tracking disclosure gates.

### EP06 — LLM routing + policy engine
**Goal:** Implement model calls as *advisory* with strict schemas and authoritative gates.
**Primary outputs:** classifier, tier2 verifier, policy engine, threshold config.

### EP07 — FAQ automation renderer + templates
**Goal:** Render templates from `templates_v1.yaml` + brand constants and send safe replies.
**Primary outputs:** template renderer, template catalog enforcement, per-channel variants.

### EP08 — Security + observability hardening (production readiness)
**Goal:** Enforce PII controls, webhook auth, monitoring, alarms, and kill switch.
**Primary outputs:** redaction, token rotation support, dashboards/alerts, audit hooks.

### EP09 — Testing + staged rollout
**Goal:** Prove readiness with smoke tests, load tests, and progressive enablement.
**Primary outputs:** CI gates, integration tests, staging run, first production deploy checklist.

---

## Recommended sequencing (short)
1. EP01 → EP02 → EP03 (foundation + core)
2. EP04 + EP06 (routing)
3. EP07 + EP05 (automation)
4. EP08 (hardening)
5. EP09 (release)

See dependency graph: `01_Work_Breakdown/Dependency_Map.md`.
