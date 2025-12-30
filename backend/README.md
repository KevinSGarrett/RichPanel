# Backend (middleware runtime) — Phase 0 Scaffold

This folder will contain the production middleware runtime code.

## Intended module layout (subject to change during implementation)
- `src/richpanel_middleware/ingest/` — webhook ingestion + ACK-fast + validation
- `src/richpanel_middleware/routing/` — LLM routing pipeline + confidence scoring + gating
- `src/richpanel_middleware/automation/` — FAQ automations (order status first)
- `src/richpanel_middleware/safety/` — PII handling, prompt-injection defense, kill switches
- `src/richpanel_middleware/storage/` — idempotency keys, state models (DynamoDB etc.)
- `src/richpanel_middleware/integrations/` — Richpanel + ecommerce (Shopify, etc.)
- `src/richpanel_middleware/observability/` — metrics/events/logging hooks
- `src/richpanel_middleware/config/` — env/config loading

## Key docs
- Routing: `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- Decision pipeline: `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- Automation: `docs/05_FAQ_Automation/Order_Status_Automation.md`
- Security: `docs/06_Security_Privacy_Compliance/`

