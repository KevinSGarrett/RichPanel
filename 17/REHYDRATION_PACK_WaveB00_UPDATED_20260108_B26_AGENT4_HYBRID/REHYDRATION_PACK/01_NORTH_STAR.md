# North Star (Immutable)

This file is the **shortest possible** statement of what we are building and what must not drift.

## Product goal
Build a middleware for Richpanel that:
- routes inbound customer messages to the correct department/team using an LLM + confidence scoring
- automates top FAQs safely (starting with order status & tracking)
- falls back to humans when confidence is low or missing data exists
- applies defense-in-depth (idempotency, rate limits, PII handling, prompt-injection controls, kill switches)

## MVP definition (v1)
**MVP is “done” when:**
- Department routing works for the defined departments and chargebacks queue with measurable accuracy + safe fallbacks
- Order-status automation works end-to-end for the defined ecommerce sources, with safe fallback
- Observability exists (basic metrics + logs + audit trail)
- Safety gates are enforced (PII policy, injection controls, kill switch)
- A repeatable deployment pipeline exists (dev/staging/prod)

## Non-negotiable constraints
- No silent drift from documented requirements
- No unsafe automation when confidence is low or required data is missing
- No PII leakage into logs/prompts/vector store beyond the defined policy
- Always keep indexes current (no orphan files)

## Canonical docs (deep detail)
- `docs/01_Product_Scope_Requirements/Product_Vision_and_Non_Goals.md`
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/06_Security_Privacy_Compliance/`

