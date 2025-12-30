# Contract Tests and Schema Validation

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

The middleware depends on **contracts** that must not silently drift:
- inbound webhook payload (Richpanel → middleware)
- LLM structured outputs (middleware decision objects)
- observability events (logs/metrics correlation)
- vendor API response shapes (Richpanel order linkage, tags, tickets)

Contract tests are the cheapest way to prevent “mysterious production failures.”

---

## Principles
- **Fail closed.** Invalid payload/schema output should not trigger automation.
- **Backwards-compatible parsing.** Accept additional fields; reject missing required fields.
- **Versioned schemas.** Changes require version bumps and CI gates.

---

## Contracts in this project

### A) Ingress webhook payload
**Owner:** middleware  
**Goal:** keep it minimal and stable.

Required fields (v1 recommendation):
- `ticket_id` (string)
- `event_type` (string)
- `sent_at` (ISO timestamp)
- optional: `source` / `signature` fields if available

**Contract testing**
- validate that ingress rejects:
  - missing `ticket_id`
  - payload > size limit (to prevent huge inline content)
- validate that ingress accepts:
  - minimal payload with only required fields

---

### B) LLM structured outputs
**Owner:** middleware  
**Schemas:**
- `docs/04_LLM_Design_Evaluation/schemas/mw_decision_v1.schema.json`
- `docs/04_LLM_Design_Evaluation/schemas/mw_tier2_verifier_v1.schema.json`

**Hard gates (CI)**
- invalid output rate must be 0% on eval runs
- policy invariants enforced even if the model outputs unsafe instructions

See:
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

---

### C) Observability event schema
**Owner:** middleware  
**Schema:** `docs/08_Observability_Analytics/schemas/mw_observability_event_v1.schema.json`

Contract tests ensure:
- every major code path emits a valid event
- correlation IDs are present (ticket_id, request_id, idempotency_key)
- no disallowed fields are logged (PII safety)

---

### D) Vendor API response shapes (sanitized fixtures)

We maintain **sanitized fixtures** of representative vendor responses and validate that:
- parsing logic handles missing fields safely
- behavior is fail-closed if essential data is absent

Examples:
- Richpanel order lookup returns `{}` when not linked
- Richpanel tag list contains IDs and names
- Rate limit responses include `Retry-After`

---

## Recommended CI jobs (Wave 09 baseline)

1) **Schema validation job**
- validates JSON schemas are valid and consistent

2) **Contract fixture tests**
- validates parsers against fixtures (sanitized)

3) **LLM eval gates**
- only required for prompt/model changes and nightly
- required for production prompt promotion

4) **Observability smoke**
- run a minimal “workflow” and verify events validate against schema

---

## Change management rule
If you change any contract:
- bump the contract version (schema file name or version field)
- update contract tests
- update `Decision_Log.md`
- update `Docs_Impact_Map` for the wave

This keeps changes traceable and reduces drift.
