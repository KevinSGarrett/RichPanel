# Security Controls Matrix (v1)

Last updated: 2025-12-22

This matrix maps key threats to the required control(s) and where they are enforced.

| Threat / risk | Required controls | Where enforced (plan) | Verification (plan) |
|---|---|---|---|
| Webhook spoofing / unauthorized calls | Auth (HMAC or token), request schema validation, API throttling, WAF rate limit (prod) | `Webhook_Auth_and_Request_Validation.md`, `AWS_Security_Baseline_Checklist.md` | unit tests (auth), integration tests, WAF/API metrics |
| Replay attacks | Timestamp window (HMAC option), idempotency keys, bounded retries | `Webhook_Auth_and_Request_Validation.md`, `../02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md` | replay simulation test, idempotency tests |
| Automation loops | `mw-routing-applied` guard, action-level idempotency, Richpanel automation guard conditions | `../03_Richpanel_Integration/Idempotency_Retry_Dedup.md`, Wave 03 docs | integration tests with loop scenarios |
| Duplicate events / retries | Event idempotency table, worker dedup, DLQ | `../02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`, `AWS_Security_Baseline_Checklist.md` | unit tests + load tests |
| PII leakage in logs | Redaction before logging, metadata-only logs, limited retention | `PII_Handling_and_Redaction.md`, `Logging_Metrics_Tracing.md`, `Data_Retention_and_Access.md` | log sampling checks, CI tests for redaction |
| Wrong customer disclosure (order/tracking) | Tier 2 deterministic match gate + verifier, “ask for order #” fallback | `../04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`, `../05_FAQ_Automation/Order_Status_Automation.md` | eval gates, unit tests |
| LLM prompt injection | System constraints + schema validation + policy engine overrides | Wave 04 docs (`Decision_Pipeline_and_Gating.md`, safety suite) | adversarial test suite |
| Excessive automation harm | **Kill switch** + safe mode route-only, template-level disable | `Kill_Switch_and_Safe_Mode.md` | functional tests, runbook drill |
| Credential leak (OpenAI/Richpanel/Shopify) | Secrets Manager, no secrets in code, rotation runbook, secret scanning | `Secrets_and_Key_Management.md`, `Secure_SDLC_and_Security_Testing.md` | secret scan in CI, rotation drill |
| Vendor outage / rate-limit storms | Backpressure, bounded retries, safe mode, DLQ | `../07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`, `Kill_Switch_and_Safe_Mode.md` | chaos test in staging, alarm verification |
| Unbounded cost / abuse | API throttling/WAF, reserved concurrency, budgets/alarms | `AWS_Security_Baseline_Checklist.md`, `../07_Reliability_Scaling/Cost_Model.md` | budget alarms, cost anomaly review |
| Unauthorized internal access | IAM least privilege, environment separation, audit logs | `IAM_Least_Privilege.md`, `Data_Retention_and_Access.md` | access reviews, CloudTrail |
| Data retention non-compliance | TTLs, retention policy, deletion process | `Data_Retention_and_Access.md` | periodic audits |
