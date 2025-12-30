# Test Data and Fixtures

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

This document explains what data we use for tests and how we keep it safe.

---

## Data sources
1) **SC_Data_ai_ready_package.zip**
   - Real historic customer messages + agent responses.
   - Used for offline evaluation and test-case generation.
   - Must be treated as **sensitive** (contains customer identifiers).

2) **Golden set (curated + labeled)**
   - Built according to: `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
   - Used for CI regression gates and weekly quality monitoring.

3) **Synthetic fixtures**
   - Minimal JSON examples for webhook payloads, Richpanel responses, Shopify responses.
   - Prefer synthetic where possible to reduce PII risk.

---

## Redaction requirements
- Any dataset copied into the test repo must be:
  - redacted (emails/phones/order numbers/tracking numbers/links)
  - minimized (only fields needed for tests)
- No raw transcripts in logs or CI artifacts.

See:
- `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`

---

## Fixture strategy
- Keep fixtures versioned under a dedicated folder (implementation repo).
- Fixtures should include:
  - success responses
  - empty / missing field responses
  - 429 responses with Retry-After
  - 500 responses
- Validate fixtures against contract tests.

---

## Labeling strategy for QA
When creating test cases from real messages:
- store only:
  - message text (redacted)
  - expected intent label
  - expected tier (0/1/2)
  - expected team/tag destination
  - expected template_id (if any)
- do not store agent names, addresses, or payment details

---

## Using SC_Data safely in dev/staging
- Dev: use redacted subset
- Staging: do not replay real customer messages into Richpanel or send any auto-replies based on real messages

---

## Exit criteria (Wave 09)
Wave 09 considers “test data plan” complete when:
- golden set SOP is referenced and implemented as a plan
- redaction rules are explicit
- fixture strategy is defined and linked to contract tests
