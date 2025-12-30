# System Overview

Last verified: 2025-12-29 — Wave F05 (foundation documentation set hardened).

This document is the **top-level “what are we building”** overview for the Richpanel AI automation system.
It is intentionally short and heavily linked so AI agents can retrieve details without exhausting context.

## Goals
- Automate high-confidence support intents (starting with FAQ / order-status style requests).
- Route all incoming tickets to the correct department with explainable reasoning and guardrails.
- Keep humans in control via explicit escalation, kill switches, audit trails, and safe defaults.

## High-level architecture
Primary reference:
- `docs/02_System_Architecture/Architecture_Overview.md`
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`

Expected v1 shape (serverless-first):
1. **Ingress**: Richpanel webhook → API Gateway → “ACK-fast” Lambda
2. **Queueing**: SQS FIFO (with DLQ) for durable, ordered processing
3. **Processing**: Worker Lambda(s) for routing + automation decisioning
4. **State**: DynamoDB for idempotency + workflow state
5. **Integrations**: Richpanel API client, ecommerce provider APIs (e.g., Shopify)
6. **Observability**: CloudWatch logs/metrics + tracing; structured event schema
7. **Security**: AWS Secrets Manager, webhook auth, request validation, PII minimization

## Where to find key details (AI retrieval map)
- **System matrix (components ↔ code ↔ docs ↔ tests):**
  - `docs/02_System_Architecture/System_Matrix.md`
- **Data flow and state:**
  - `docs/02_System_Architecture/Data_Flow_and_Storage.md`
  - `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
- **Richpanel integration:**
  - `docs/03_Richpanel_Integration/INDEX.md`
  - `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
  - Vendor doc crosswalk: `docs/03_Richpanel_Integration/Vendor_Doc_Crosswalk.md`
- **API contracts (our system):**
  - `docs/04_API_Contracts/API_Reference.md`
  - `docs/04_API_Contracts/openapi.yaml`
- **Security & privacy:**
  - `docs/06_Security_Privacy_Compliance/README.md`
  - `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`
- **Testing strategy + evidence:**
  - `docs/08_Testing_Quality/Test_Strategy_and_Matrix.md`
  - `docs/08_Testing_Quality/Test_Evidence_Log.md`

## Operational philosophy
- Prefer **safe routing** over risky automation.
- Use **confidence thresholds** and **explicit “never automate” rules**.
- Preserve **auditability**: every automated decision should be reconstructable.
- Keep prompts and context **minimal**; link to canonical docs instead of duplicating.

## Change control
When the architecture changes, update:
- `docs/02_System_Architecture/System_Matrix.md`
- `docs/04_API_Contracts/openapi.yaml` (if endpoints change)
- `CHANGELOG.md`
