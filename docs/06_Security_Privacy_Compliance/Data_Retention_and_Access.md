# Data Retention and Access Controls (v1)

Last updated: 2025-12-22

This document defines:
- **how long** we retain any data we control
- **who** can access it
- **how** deletion requests are handled

Design goal: retain the *minimum* necessary for reliability and incident response, while reducing privacy risk.

---

## 1) Retention policy (v1 defaults)

### 1.1 Middleware operational state (AWS)
| Data store | What it contains | Default retention | Why |
|---|---|---:|---|
| DynamoDB idempotency table | event/action keys (no message text) | 30 days (TTL) | prevents duplicates + supports investigations |
| DynamoDB conversation state table | minimal workflow state | 7 days (TTL) | supports short-lived flows |
| SQS DLQ | failed events | 14 days (SQS max) | debugging + replay |
| CloudWatch logs | metadata logs (redacted) | 30 days | incident response + debugging |
| Metrics (CloudWatch) | aggregated metrics | 15 months (AWS default) | trend analysis (no PII) |

### 1.2 Evaluation artifacts (non-production)
| Data store | What it contains | Default retention | Notes |
|---|---|---:|---|
| S3 “eval-artifacts” (optional) | redacted datasets + metrics outputs | 90 days | must be redacted; restricted access |
| Local dev artifacts | redacted only | developer-managed | no raw exports |

**If raw (unredacted) data ever exists, retention must be near-zero and access must be extremely restricted. Prefer: never store raw.**

---

## 2) Access control model

### 2.1 Principle
- default deny
- least privilege
- prod access is restricted

### 2.2 Who can access what (recommended)
| Resource | Allowed roles |
|---|---|
| Prod Secrets Manager secrets | owner + security admin only |
| Prod CloudWatch logs | on-call engineers + security admin |
| Non-prod logs/secrets | developers |
| Eval artifact bucket | limited ML/eval operators |

### 2.3 Break-glass procedure (required)
If emergency access is needed:
- time-bound access grant
- recorded in incident notes
- rotate affected secrets after incident if exposure is possible

---

## 3) Deletion requests (customer privacy)
Even if we store minimal data, we must handle deletion requests.

### 3.1 What we may store that is “customer-linked”
- hashed or partial identifiers (email hash, last-4 order id)
- ticket IDs (L2) which can be linked back to a customer by Richpanel

### 3.2 Deletion procedure (v1)
1) Identify relevant ticket_id(s) / customer identifiers from Richpanel
2) Delete matching records in:
   - conversation state table (if still present)
   - any eval artifact set (if we created one)
3) Verify nothing else remains beyond immutable vendor logs we do not control
4) Document completion

**Note:** We cannot delete data retained by vendors (OpenAI/Richpanel/Shopify); we can only reduce what we send/store.

---

## 4) Retention configuration checklist (deployment)
- DynamoDB TTL enabled on idempotency + state tables
- CloudWatch log retention explicitly set (not “never expire”)
- S3 lifecycle rules applied (if used)
- Access policies reviewed and approved
