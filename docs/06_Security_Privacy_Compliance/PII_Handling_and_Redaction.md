# PII Handling and Redaction (v1 Policy)

Last updated: 2025-12-22

This policy applies to all customer data processed by the middleware (inbound Richpanel messages, order lookups, and outbound automated replies).

Even if we are not handling “ultra-sensitive” identifiers (SSN/DL), **emails, phone numbers, order numbers, and tracking links/numbers are still personal data** and must be handled safely.

---

## 1) Primary risks we must prevent
1) **Wrong-customer disclosure**  
   Sending tracking/order info that belongs to a different customer.

2) **PII leakage via logs**  
   Logging full messages or identifiers into CloudWatch/observability tools.

3) **Over-sharing to the LLM**  
   Sending unnecessary PII to OpenAI, or storing model inputs/outputs.

---

## 2) Core rules (required)

### Rule A — Deterministic match before Tier 2 disclosure
We only disclose order/tracking information when we have a deterministic match between:
- the Richpanel ticket/customer context, and
- a single order record (Richpanel-linked order or Shopify order)

If not deterministic:
- send a **Tier 1** intake message (“please provide order # / email / phone”), and
- route to humans.

### Rule B — Don’t store raw conversation content by default
- Do **not** store full message bodies in DynamoDB.
- If temporary message storage is needed for retries:
  - store a redacted + truncated version
  - apply TTL

### Rule C — Redact before logging
Logs are the #1 leak vector. We must redact:
- email addresses
- phone numbers
- order numbers
- tracking numbers/URLs
- addresses (if ever present)

### Rule D — Do not log OpenAI request/response bodies
Log only:
- model name/version
- token usage (if available)
- response validity (schema pass/fail)
- output summary fields (intent, template_id, confidence)
- correlation IDs

### Rule E — Evaluation datasets must be redacted
Any dataset derived from real customer messages must:
- be redacted to remove PII
- not include full tracking URLs
- be stored in restricted-access buckets/folders
- be deleted on request when feasible

---

## 3) Redaction patterns (v1)
Minimum patterns:
- Emails → `[EMAIL]`
- Phone numbers → `[PHONE]`
- Order IDs → `[ORDER_ID]` (optional: keep last-4 as `[ORDER_ID:*1234]`)
- Tracking numbers/URLs → `[TRACKING]`
- Addresses (if present) → `[ADDRESS]`

**Important:** redaction must happen **before** logs are written.

---

## 4) What the LLM is allowed to see (minimization)
Allowed:
- customer message text (redacted if possible)
- channel type (livechat/email)
- allowed departments + allowed template IDs
- minimal order context if needed for classification (status label only, not address/payment)

Not allowed:
- full customer profile objects
- shipping address
- payment details
- internal secrets / tokens
- internal dashboards/URLs that include credentials

---

## 5) Operational access controls
- Only the smallest operator set can access prod logs/metrics.
- Debug logging of message text is **disabled in prod** by default.
- Any “break glass” access must be time-bound and recorded.

---

## 6) Retention (v1 defaults)
- DynamoDB idempotency keys: 7–30 days (enough for replay protection + debugging)
- DynamoDB conversation state: 1–7 days TTL (workflow only)
- CloudWatch logs: 14–30 days (short by default, extend only if required)
- Redacted eval artifacts: 30–90 days (or shorter)

Exact numbers are finalized in `Data_Retention_and_Access.md`.

---

## 7) “Done” definition for this policy
This policy is considered implemented when:
- logging redaction is enforced and verified (sample log review)
- LLM requests use minimal data and do not include identifiers unnecessarily
- automation gates prevent disclosure without deterministic match
- retention and deletion procedures are documented and operational
