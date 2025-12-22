# Encryption and Data Protection

Last updated: 2025-12-22

This document defines the encryption posture for the middleware.

---

## 1) In transit (required)
- All inbound webhook traffic uses HTTPS (TLS via API Gateway).
- All outbound API calls (OpenAI/Richpanel/Shopify) use HTTPS with TLS verification.

---

## 2) At rest (required)
Enable encryption at rest for all AWS storage components:
- DynamoDB tables (AWS-owned key ok; KMS CMK recommended for prod)
- SQS queues (SSE)
- CloudWatch logs (default; consider KMS CMK for strict compliance)
- S3 buckets (if used for artifacts)

---

## 3) KMS key strategy (recommended)
- Separate keys per environment (dev/stage/prod)
- Restrict key usage by IAM conditions
- Enable key rotation for CMKs where applicable

---

## 4) Data handling constraints
- Do not store full message bodies by default.
- Do not store OpenAI request/response bodies (only metadata).
- Tracking details are only disclosed to customer when deterministic match exists.

---

## 5) Backups
If we store any durable state:
- DynamoDB PITR recommended for prod state tables (idempotency/state)
- S3 versioning if we store evaluation artifacts

(Backups must not increase retention risk; retention policy still applies.)
