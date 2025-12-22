# AWS Security Baseline Checklist (v1)

Last updated: 2025-12-22  
Applies to: **AWS region `us-east-2`**, serverless stack (API Gateway → Lambda → SQS FIFO → Lambda → DynamoDB)

This checklist is the **minimum security baseline** for production.  
It is written so it can be executed even **without Control Tower** (Organizations-only).

> **Principle:** Prefer **simple, hard-to-misconfigure** controls for v1.  
> Anything “nice-to-have” is marked as optional.

---

## 0) Ownership and environments

**Recommended environments (separate AWS accounts):**
- `dev` (non-prod)
- `staging` (pre-prod)
- `prod` (production)

**Owner (management account):** Developer (you)

---

## 1) AWS account & org baseline (required)

### 1.1 Root account hygiene (each account)
- [ ] Root user has **MFA enabled**
- [ ] Root credentials stored in a company-controlled password manager
- [ ] Root access is *not* used for daily operations
- [ ] **Alternate contacts** (billing/operations/security) configured
- [ ] Account-level **billing alerts** enabled

### 1.2 AWS Organizations baseline (management account)
- [ ] AWS Organizations created
- [ ] Separate accounts created (`dev`, `staging`, `prod`)
- [ ] Consolidated billing enabled (default)
- [ ] **Service control policies (SCPs)**: *minimal v1 guardrails*
  - [ ] Deny leaving the org (prevent “account escape”)
  - [ ] Deny disabling CloudTrail
  - [ ] Deny deleting log buckets (if centralized logs used)
  - [ ] Deny creating access keys for root

> Optional later: Control Tower (guardrails + account factory). Not required for v1.

---

## 2) Identity and Access Management (IAM) baseline

### 2.1 Human access (required)
- [ ] Use **AWS IAM Identity Center (SSO)** for console access (recommended)
- [ ] No long-lived IAM user access keys for humans (prefer SSO)
- [ ] Enforce MFA for all privileged roles
- [ ] Separate roles for:
  - [ ] deployment/CI
  - [ ] read-only support/debug
  - [ ] break-glass admin

### 2.2 Service roles (required)
- [ ] Separate Lambda execution roles for:
  - [ ] `mw-ingress` (minimal permissions)
  - [ ] `mw-worker` (only what is needed)
- [ ] Least privilege policy documents (no `*` actions/resources unless justified)
- [ ] Use resource-level constraints where possible (table ARNs, queue ARNs)

### 2.3 IAM visibility (recommended)
- [ ] Enable **IAM Access Analyzer** (at least in prod)
- [ ] Review public/shared resources quarterly

---

## 3) Secrets and key management (required)

- [ ] All vendor secrets stored in **AWS Secrets Manager**
  - Richpanel API key
  - OpenAI API key
  - Shopify token (if used)
- [ ] Secrets are *not* hardcoded in code or stored in env files
- [ ] Rotation approach defined:
  - [ ] manual rotation accepted for v1 (document procedure)
  - [ ] automatic rotation optional later (if vendor supports)
- [ ] KMS key policy reviewed (defaults ok for v1, avoid broad principals)

---

## 4) API perimeter protection (required)

### 4.1 API Gateway settings
- [ ] HTTPS only
- [ ] Request size limits (default is fine; document max)
- [ ] Enable request validation where possible (basic schema)
- [ ] Throttling configured (rate + burst)
- [ ] Access logs enabled (PII-safe fields only)

### 4.2 Webhook authentication
- [ ] Webhook requires auth (choose best supported):
  - [ ] **Header token** (`X-Middleware-Token`) OR
  - [ ] HMAC signature w/ timestamp (preferred) OR
  - [ ] URL token (fallback only)
- [ ] Reject missing/invalid auth with 401
- [ ] Reject invalid JSON / missing required fields with 400

### 4.3 AWS WAF (recommended for prod)
- [ ] Attach AWS WAF to API Gateway (or CloudFront in front)
- [ ] Add a **rate-based rule** (baseline protection against abuse)
- [ ] Add managed rule set(s) (baseline):
  - [ ] AWSManagedRulesCommonRuleSet
  - [ ] AWSManagedRulesKnownBadInputsRuleSet

> If WAF is not used in v1, API Gateway throttling + token auth becomes even more critical.

---

## 5) Lambda security baseline (required)

### 5.1 Configuration
- [ ] Reserved concurrency set (prevents runaway costs and protects downstream rate limits)
- [ ] Timeouts set appropriately:
  - ingress: short (fast ACK)
  - worker: longer (but bounded)
- [ ] Environment variables **do not** contain secrets (Secrets Manager only)
- [ ] Logs are structured JSON and redacted

### 5.2 Invocation safety
- [ ] Idempotency enforced (DynamoDB conditional writes)
- [ ] Fail-closed behavior: if uncertain → route-only
- [ ] Safe-mode / automation kill switch implemented (see Kill Switch doc)

---

## 6) SQS baseline (required)

- [ ] Use **SQS FIFO** (message group = `conversation_id`)
- [ ] SSE enabled (SQS-managed or KMS)
- [ ] DLQ configured and alarmed
- [ ] Redrive policy set with bounded retries (e.g., 3–5)
- [ ] Visibility timeout > worker timeout (to avoid duplicate processing)

---

## 7) DynamoDB baseline (required)

- [ ] Encryption at rest enabled (default is fine; KMS optional)
- [ ] TTL enabled for:
  - idempotency keys
  - conversation state
- [ ] Point-in-time recovery (PITR) enabled in prod (recommended)
- [ ] Alarms/monitoring for throttles and errors

---

## 8) Logging, monitoring, and alerting (required)

### 8.1 Logs
- [ ] CloudWatch Log Group retention set:
  - dev/staging: shorter
  - prod: longer (but finite)
- [ ] CloudTrail enabled (all regions) in prod
- [ ] No PII in logs (redaction enforced)

### 8.2 Alarms (minimum)
- [ ] API Gateway 5xx spike
- [ ] Lambda error rate spike (ingress + worker)
- [ ] Lambda throttles / concurrency saturation
- [ ] SQS DLQ depth > 0 (immediate attention)
- [ ] SQS age of oldest message rising
- [ ] DynamoDB throttles
- [ ] Budget alarm (daily + monthly)

### 8.3 Optional security services
- [ ] GuardDuty enabled (prod recommended)
- [ ] Security Hub enabled (optional v1, recommended later)
- [ ] AWS Config enabled (optional v1)

---

## 9) Evidence checklist (what “done” looks like)

For v1 readiness, capture:
- screenshots or IaC outputs showing:
  - [ ] MFA enabled
  - [ ] WAF/Throttle enabled (prod)
  - [ ] DLQ configured + alarm
  - [ ] log retention configured
  - [ ] Secrets Manager populated (no plaintext secrets in repo)
- a short runbook proving:
  - [ ] how to rotate a secret
  - [ ] how to enable safe mode / disable automation

---

## Appendix: Recommended owners per task (default)
- AWS org/account setup: **Developer (you)**  
- Richpanel configuration: Support Ops / Admin + Developer  
- Secrets rotation: Developer + Support Ops (as needed)  
- Incident response: Developer + Leadership (for customer-impact incidents)

---

## 9) Monitoring, alarms, and emergency controls (required)
- [ ] Minimum alarms + dashboards configured: `Security_Monitoring_Alarms_and_Dashboards.md`
- [ ] Kill switch / safe mode implemented and tested: `Kill_Switch_and_Safe_Mode.md`
- [ ] Webhook token rotation runbook available: `Webhook_Secret_Rotation_Runbook.md`
- [ ] Break-glass role and alerting configured: `IAM_Access_Review_and_Break_Glass.md`