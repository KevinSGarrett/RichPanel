# Implementation Sequence (Sprints) — Wave 12

Last updated: 2025-12-23

This is a **best‑suggested** implementation sequence that turns the Wave 12 epics/tickets into a sprint plan.

> Notes
> - “Points” are relative sizing estimates (use them to balance workload, not as a promise).
> - Sprint length is flexible. The plan assumes **Sprint 0 is short** (preflight) and Sprints 1–5 are standard development sprints.
> - This plan is optimized for **shipping safely**: routing first, then limited automation, then progressive rollout.

---

## Sprint summary

| Sprint | Est. points | Primary outcomes |
|---|---:|---|
| Post‑v1 backlog | 8 | Optional enhancements that are not required for initial production routing/automation. |
| Sprint 0 — Preflight | 16 | Confirm access + tenant capabilities; create required Richpanel teams/tags; choose webhook auth approach. |
| Sprint 1 — Foundation | 21 | Create AWS accounts/roles/secrets; pick IaC; build CI gates so every change is safe-by-default. |
| Sprint 2 — Core pipeline | 32 | Deploy serverless ingestion + queue + worker skeleton with idempotency/state, feature flags, and baseline observability. |
| Sprint 3 — Richpanel routing + LLM route-only | 45 | Implement Richpanel action layer + LLM routing policy engine; ship **route-only** end-to-end in staging. |
| Sprint 4 — Automation + order status + security baseline | 43 | Add Tier 1 safe-assist and Tier 2 verified order-status automation; enforce redaction + auth + dashboards. |
| Sprint 5 — Testing + rollout | 34 | Execute smoke + load/soak; perform first production deploy (routing-only) and progressive enablement; finalize ops hardening. |

---

## Critical path (v1)

1. **Preflight + tenant verification** (Sprint 0) → confirm webhook auth constraints + order linkage reality.
2. **AWS/IaC/CI foundation** (Sprint 1) → safe deploy pipeline.
3. **Core pipeline deployed** (Sprint 2) → ingestion + queue + worker + idempotency + flags + logs.
4. **Route-only end‑to‑end** (Sprint 3) → Richpanel actions + LLM routing + policy gates.
5. **Automation enablement** (Sprint 4) → Tier 1 safe-assist + Tier 2 verified order status.
6. **Testing + progressive rollout** (Sprint 5) → staging smoke/load; production routing-only → enable Tier 1 → enable Tier 2.

---

## Sprint-by-sprint ticket plan

### Sprint 0 — Preflight

**Goal:** Confirm access + tenant capabilities; create required Richpanel teams/tags; choose webhook auth approach.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP00-T001` — Inventory required access + secrets (Richpanel API key, Shopify access) and define secret storage plan | 2 | P0 | V1 |  |
| `W12-EP00-T002` — Verify Richpanel tenant automation capabilities needed for middleware trigger (deferred Wave 03 items) | 2 | P0 | V1 | Required before enabling production automation. |
| `W12-EP00-T003` — Sample order linkage reality in tenant (Richpanel order endpoints) without storing PII | 3 | P0 | V1 | Required before enabling production automation. |
| `W12-EP00-T004` — Finalize webhook authentication approach and rotation strategy (based on tenant verification) | 2 | P0 | V1 | Required before enabling production automation. |
| `W12-EP01-T010` — Set up AWS Organization and create dev/staging/prod accounts (Organizations-only) | 5 | P0 | V1 |  |
| `W12-EP04-T040` — Create Richpanel team + tags (Chargebacks/Disputes, mw-routing-applied, feedback tags) and document mapping | 2 | P0 | V1 |  |

### Sprint 1 — Foundation

**Goal:** Create AWS accounts/roles/secrets; pick IaC; build CI gates so every change is safe-by-default.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP01-T011` — Create IAM roles and least-privilege policies for middleware (ingress vs worker) and CI deploy | 5 | P0 | V1 |  |
| `W12-EP01-T012` — Enable baseline logging + audit (CloudTrail, CloudWatch log retention, budgets, alarms) | 3 | P0 | V1 |  |
| `W12-EP01-T013` — Create Secrets Manager + SSM parameter namespaces for env config (including kill switch flags) | 3 | P0 | V1 |  |
| `W12-EP02-T020` — Select IaC tool and scaffold infrastructure repo modules (serverless stack) | 5 | P0 | V1 |  |
| `W12-EP02-T021` — Create CI pipeline with quality gates (unit tests, schema validation, lint, security checks) | 5 | P0 | V1 |  |

### Sprint 2 — Core pipeline

**Goal:** Deploy serverless ingestion + queue + worker skeleton with idempotency/state, feature flags, and baseline observability.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP02-T022` — Implement deployment promotion flow (dev → staging → prod) and rollback automation | 5 | P0 | V1 |  |
| `W12-EP03-T030` — Implement API Gateway + ingress Lambda (fast ACK, validation, enqueue) | 5 | P0 | V1 |  |
| `W12-EP03-T031` — Provision SQS FIFO + DLQ and internal message schema (conversation-ordered processing) | 3 | P0 | V1 |  |
| `W12-EP03-T032` — Create DynamoDB tables for idempotency + minimal conversation state with TTL | 3 | P0 | V1 |  |
| `W12-EP03-T033` — Implement worker Lambda skeleton (dequeue, fetch context, decision pipeline placeholder, action stub) | 5 | P0 | V1 |  |
| `W12-EP03-T034` — Implement runtime feature flags (safe_mode, automation_enabled, per-template toggles) with caching | 3 | P0 | V1 |  |
| `W12-EP03-T035` — Implement observability event logging + correlation IDs (ingress and worker) | 3 | P0 | V1 |  |
| `W12-EP03-T036` — Implement vendor retry/backoff utilities and concurrency bounds (prevent rate-limit storms) | 5 | P0 | V1 |  |

### Sprint 3 — Richpanel routing + LLM route-only

**Goal:** Implement Richpanel action layer + LLM routing policy engine; ship **route-only** end-to-end in staging.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP04-T041` — Configure Richpanel automation to trigger middleware on inbound customer messages (avoid loops) | 3 | P0 | V1 |  |
| `W12-EP04-T042` — Implement Richpanel API client with retries, pagination, and rate-limit handling | 5 | P0 | V1 |  |
| `W12-EP04-T043` — Implement action executor (route/tag/assign/reply) with action-level idempotency keys | 8 | P0 | V1 |  |
| `W12-EP04-T044` — Build integration test harness for Richpanel actions (staging recommended) | 5 | P0 | V1 |  |
| `W12-EP06-T060` — Implement classifier model call with strict schema validation (mw_decision_v1) and fail-closed fallback | 5 | P0 | V1 |  |
| `W12-EP06-T061` — Implement policy engine (Tier 0 overrides, Tier 2 eligibility, Tier 3 disabled) as authoritative layer | 5 | P0 | V1 |  |
| `W12-EP06-T062` — Implement Tier 2 verifier call (mw_tier2_verifier_v1) and integrate into policy gating | 5 | P0 | V1 |  |
| `W12-EP06-T063` — Implement confidence threshold configuration + calibration workflow hooks | 3 | P1 | V1 |  |
| `W12-EP07-T070` — Implement template renderer (YAML templates + brand constants) with safe placeholder handling | 3 | P0 | V1 |  |
| `W12-EP07-T071` — Enforce template catalog: allowed template_ids, per-channel enablement, per-template feature flags | 3 | P0 | V1 |  |

### Sprint 4 — Automation + order status + security baseline

**Goal:** Add Tier 1 safe-assist and Tier 2 verified order-status automation; enforce redaction + auth + dashboards.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP05-T050` — Implement deterministic order linkage lookup using Richpanel order endpoints | 5 | P0 | V1 |  |
| `W12-EP05-T051` — Map order details into template variables and handle common edge cases (multiple fulfillments) | 5 | P0 | V1 |  |
| `W12-EP05-T053` — Define and implement order-status-related routing rules (DNR, missing items, refund requests) | 3 | P0 | V1 |  |
| `W12-EP07-T072` — Implement Tier 1 safe-assist automation playbooks (DNR, missing items intake, refunds intake) + routing tags | 5 | P0 | V1 |  |
| `W12-EP07-T073` — Implement Tier 2 verified order status auto-reply (tracking link/number) with deterministic match + verifier approval | 8 | P0 | V1 |  |
| `W12-EP07-T074` — Enforce 'auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)' invariant across all automation paths | 2 | P0 | V1 |  |
| `W12-EP08-T080` — Implement webhook authentication in ingress (header token preferred) + request schema validation | 5 | P0 | V1 |  |
| `W12-EP08-T081` — Implement PII redaction enforcement + tests (logs, traces, eval artifacts) | 5 | P0 | V1 |  |
| `W12-EP08-T082` — Deploy dashboards + alarms (Wave 06/07/08 alignment) and validate alert runbooks | 5 | P0 | V1 |  |

### Sprint 5 — Testing + rollout

**Goal:** Execute smoke + load/soak; perform first production deploy (routing-only) and progressive enablement; finalize ops hardening.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP06-T064` — Integrate offline eval harness into CI (golden set run + regression gates) | 5 | P1 | V1 |  |
| `W12-EP07-T075` — Create Richpanel 'AUTO:' macros aligned to template IDs (ops task) and document governance | 2 | P1 | V1 | Ops quality-of-life; not required for automation to send replies. |
| `W12-EP08-T083` — Harden public endpoint (API Gateway throttling, optional WAF, SSRF/egress controls) | 5 | P0 | V1 | Includes throttling (required) + optional WAF (recommended). |
| `W12-EP08-T084` — Implement secret rotation support (multi-token validation) + document operational steps | 3 | P1 | V1 |  |
| `W12-EP08-T085` — Operationalize IAM access reviews and break-glass workflow (alerts + cadence) | 3 | P1 | V1 |  |
| `W12-EP09-T090` — Implement and run smoke test pack in staging (routing + Tier1 + Tier2 + Tier0 + kill switch) | 3 | P0 | V1 |  |
| `W12-EP09-T091` — Run load/soak tests and validate backlog catch-up behavior without vendor storms | 5 | P1 | V1 |  |
| `W12-EP09-T092` — Execute first production deploy runbook (routing-only) and verify observability + rollback | 3 | P0 | V1 |  |
| `W12-EP09-T093` — Progressive enablement: enable Tier 1 templates first, then Tier 2 order status after verification | 3 | P0 | V1 |  |
| `W12-EP09-T094` — Establish post-launch governance cadence (weekly review, monthly calibration) and close the loop with agent feedback tags | 2 | P1 | V1 |  |

### Post‑v1 backlog

**Goal:** Optional enhancements that are not required for initial production routing/automation.

| Ticket | Points | Priority | Scope | Notes |
|---|---:|---|---|---|
| `W12-EP05-T052` — Implement Shopify Admin API fallback (only if required and credentials exist) | 8 | P2 | POST_V1 | Only required if Richpanel order payload cannot provide tracking/status fields reliably. |


---

## Parallelization suggestions (best practice)

If you have multiple builders, the safest parallelization is:
- **Infra/DevOps** leads Sprint 1–2 (accounts, IaC, CI/CD, baseline logging)
- **Backend** leads Sprint 2–4 (pipeline, Richpanel client/actions, LLM policy engine, template renderer)
- **Support Ops / Richpanel Admin** completes the Richpanel-side configuration tickets early (Sprint 0–3)

---

## What “done” looks like (v1)

- **Routing works** for all inbound messages (no loops, no duplicates causing double actions).
- **Automation is gated** by policy (Tier 0 never auto, Tier 2 only with deterministic match).
- **Kill switch works** (safe_mode, automation_enabled) and runbooks/smoke tests exist.
- Observability supports “detect, diagnose, mitigate” in <15 minutes.
