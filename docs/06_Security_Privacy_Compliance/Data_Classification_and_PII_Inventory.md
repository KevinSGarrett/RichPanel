# Data Classification and PII Inventory

Last updated: 2025-12-22

This document enumerates the data we process and defines the classification rules used across:
- logging
- LLM prompts
- evaluation datasets
- storage (DynamoDB, S3)
- operational tooling (alerts, tickets)

---

## 1) Classification levels (v1)

| Level | Name | Examples | Storage/Sharing rule |
|---|---|---|---|
| L0 | Public | Documentation, generic FAQs | Can be shared freely |
| L1 | Internal | Internal routing taxonomy, template IDs | Company-only |
| L2 | Confidential | Richpanel ticket IDs, internal incident IDs | Company-only, need-to-know |
| L3 | Restricted (Customer data / PII) | Email, phone, order #, tracking links, message content | Strict minimization, redaction required, least-privilege access |

**Default:** treat all customer message content as **L3**.

---

## 2) Data inventory (what we expect to see)

| Data element | Source | Classification | Where it may appear | Handling |
|---|---|---|---|---|
| Customer message text | Richpanel | L3 | webhook, API fetch | Minimize, redact before logs, truncated in debug |
| Email | Richpanel / customer text | L3 | payload, extracted entities | Store only hashed/partial; redact in logs |
| Phone number | Richpanel / customer text | L3 | payload, extracted entities | Store only hashed/partial; redact in logs |
| Order number | customer text | L3 | extracted entities | Store only last-4 or hash; redact in logs |
| Tracking # / tracking URL | Richpanel/Shopify | L3 | order lookup results | Do not log; show to customer only when deterministic match |
| Shipping address | Shopify/Richpanel | L3 | order lookup results | **Never** disclose in v1 automation; do not log |
| Ticket/Conversation ID | Richpanel | L2 | webhook payload | Ok to log (L2) but avoid correlating with message content |
| Template ID | middleware | L1 | decision outputs | Safe to log (no PII) |
| Routing tags/team names | Richpanel/middleware | L1 | decision outputs | Safe to log |
| OpenAI request/response bodies | middleware | L3 | API calls | **Do not log** raw; log metadata only |

---

## 3) Data minimization rules (required)

### 3.1 LLM inputs
- Prefer sending **only what is required**:
  - message text (possibly redacted)
  - channel type (LiveChat/email)
  - allowed departments + allowed template IDs (no secrets)
- Never send:
  - API keys, tokens, internal URLs with credentials
  - full customer profile objects
  - shipping address, payment details

### 3.2 Logs
- Log **metadata only** by default:
  - ticket_id (L2)
  - decision summary (template_id, department_id, confidence)
  - timings, retries, error codes
- If message text must be logged for debugging:
  - redact PII first
  - truncate (e.g., first 200 chars)
  - keep in dev/staging only

### 3.3 Storage
- DynamoDB state tables:
  - store only deterministic identifiers needed for idempotency + flow
  - avoid storing message bodies (prefer not stored at all)
- If S3 is used for evaluation artifacts:
  - store only redacted datasets
  - use per-environment buckets and restricted access

---

## 4) Redaction standard (v1)
The canonical redaction rules are defined in `PII_Handling_and_Redaction.md`.

Minimum redaction patterns:
- emails → `[EMAIL]`
- phones → `[PHONE]`
- order numbers → `[ORDER_ID]` (optionally keep last-4)
- tracking #/URLs → `[TRACKING]`

---

## 5) Deletion requests (customer privacy)
Even if we do not store much data, we must support:
- deleting any stored identifiers tied to a customer request
- removing evaluation artifacts derived from their messages (if we created any)

Mechanism is documented in `Data_Retention_and_Access.md`.
