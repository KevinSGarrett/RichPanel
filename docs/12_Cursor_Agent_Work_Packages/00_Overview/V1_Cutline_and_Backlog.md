# V1 Cutline and Post‑V1 Backlog — Wave 12

Last updated: 2025-12-23

This document defines what is **required for v1** versus what can safely ship **after v1**.

## V1 goal (what we ship first)

- **Route every inbound message** to the correct department with confidence scoring.
- **Automate top FAQs** safely (Tier 1 safe-assist; Tier 2 only when deterministically verified).
- Maintain strict safety constraints: **auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)**, Tier 0 always human, PII-safe logs.

## Priorities

- **P0 (Must):** required before enabling production routing/automation.
- **P1 (Should):** strongly recommended for v1 quality and operational safety; may slip if needed.
- **P2 (Post‑v1):** optional enhancements; do not block initial production value.

## Ticket cutline table

| Ticket | Epic | Priority | Scope | Why it’s in this scope |
|---|---|---|---|---|
| `W12-EP05-T052` | EP05 | P2 | POST_V1 | Nice-to-have fallback; only needed if Richpanel order payload is insufficient (tracking/status missing or unreliable). |
| `W12-EP00-T001` | EP00 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP00-T002` | EP00 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP00-T003` | EP00 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP00-T004` | EP00 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP01-T010` | EP01 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP01-T011` | EP01 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP01-T012` | EP01 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP01-T013` | EP01 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP02-T020` | EP02 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP02-T021` | EP02 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP02-T022` | EP02 | P0 | V1 | Foundation prerequisite (access, accounts, CI, secrets) to build and deploy safely. |
| `W12-EP03-T030` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP03-T031` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP03-T032` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP03-T033` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP03-T034` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP03-T035` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP03-T036` | EP03 | P0 | V1 | Core middleware pipeline (ingestion, queue, idempotency, flags, retries, observability). |
| `W12-EP04-T040` | EP04 | P0 | V1 | Richpanel integration (trigger, API client, idempotent actions) required for routing and replies. |
| `W12-EP04-T041` | EP04 | P0 | V1 | Richpanel integration (trigger, API client, idempotent actions) required for routing and replies. |
| `W12-EP04-T042` | EP04 | P0 | V1 | Richpanel integration (trigger, API client, idempotent actions) required for routing and replies. |
| `W12-EP04-T043` | EP04 | P0 | V1 | Richpanel integration (trigger, API client, idempotent actions) required for routing and replies. |
| `W12-EP04-T044` | EP04 | P0 | V1 | Richpanel integration (trigger, API client, idempotent actions) required for routing and replies. |
| `W12-EP05-T050` | EP05 | P0 | V1 | Order-status automation requires deterministic order linkage and mapping to safe variables. |
| `W12-EP05-T051` | EP05 | P0 | V1 | Order-status automation requires deterministic order linkage and mapping to safe variables. |
| `W12-EP05-T053` | EP05 | P0 | V1 | Order-status automation requires deterministic order linkage and mapping to safe variables. |
| `W12-EP06-T060` | EP06 | P0 | V1 | LLM routing + policy engine enforces safety gates and confidence-based behavior. |
| `W12-EP06-T061` | EP06 | P0 | V1 | LLM routing + policy engine enforces safety gates and confidence-based behavior. |
| `W12-EP06-T062` | EP06 | P0 | V1 | LLM routing + policy engine enforces safety gates and confidence-based behavior. |
| `W12-EP07-T070` | EP07 | P0 | V1 | Templates/playbooks implement automation safely while keeping copy out of the model. |
| `W12-EP07-T071` | EP07 | P0 | V1 | Templates/playbooks implement automation safely while keeping copy out of the model. |
| `W12-EP07-T072` | EP07 | P0 | V1 | Templates/playbooks implement automation safely while keeping copy out of the model. |
| `W12-EP07-T073` | EP07 | P0 | V1 | Templates/playbooks implement automation safely while keeping copy out of the model. |
| `W12-EP07-T074` | EP07 | P0 | V1 | Templates/playbooks implement automation safely while keeping copy out of the model. |
| `W12-EP08-T080` | EP08 | P0 | V1 | Security/PII/endpoint hardening required before production exposure. |
| `W12-EP08-T081` | EP08 | P0 | V1 | Security/PII/endpoint hardening required before production exposure. |
| `W12-EP08-T082` | EP08 | P0 | V1 | Security/PII/endpoint hardening required before production exposure. |
| `W12-EP08-T083` | EP08 | P0 | V1 | Security/PII/endpoint hardening required before production exposure. |
| `W12-EP09-T090` | EP09 | P0 | V1 | Testing + staged rollout required for safe production enablement. |
| `W12-EP09-T092` | EP09 | P0 | V1 | Testing + staged rollout required for safe production enablement. |
| `W12-EP09-T093` | EP09 | P0 | V1 | Testing + staged rollout required for safe production enablement. |
| `W12-EP06-T063` | EP06 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |
| `W12-EP06-T064` | EP06 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |
| `W12-EP07-T075` | EP07 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |
| `W12-EP08-T084` | EP08 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |
| `W12-EP08-T085` | EP08 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |
| `W12-EP09-T091` | EP09 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |
| `W12-EP09-T094` | EP09 | P1 | V1 | Strongly recommended for v1 quality; may be scheduled later if needed. |

---

## Post‑v1 backlog (recommended next additions)

- **Shopify Admin API fallback** for tracking/status if Richpanel order payload is incomplete (`W12-EP05-T052`).
- Optional **WAF** in front of API Gateway (recommended once stable).
- Separate “priority lane” for LiveChat if p95 routing latency misses targets.
- Multi-region DR if business continuity requirements increase.

## How to use this cutline

1. Build all **P0** items first.
2. Pull **P1** items forward whenever they reduce risk (security/testing/observability).
3. Only start **P2** after v1 is stable and measured.