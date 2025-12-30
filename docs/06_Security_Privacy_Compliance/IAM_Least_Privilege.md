# IAM Least Privilege (AWS)

Last updated: 2025-12-22

This document defines recommended IAM role separation and least-privilege policies for the serverless stack.

Related:
- Access review + break-glass: `IAM_Access_Review_and_Break_Glass.md`
- AWS baseline checklist: `AWS_Security_Baseline_Checklist.md`


Stack baseline:
API Gateway → Lambda (Ingress) → SQS FIFO → Lambda (Worker) → DynamoDB (+ Secrets Manager)

---

## 1) Roles (recommended)
### 1.1 Ingress Lambda role (rp-mw-ingress)
Permissions should be limited to:
- `sqs:SendMessage` to the inbound FIFO queue
- `dynamodb:PutItem` / `dynamodb:UpdateItem` to idempotency table (conditional writes)
- `secretsmanager:GetSecretValue` (webhook secret if needed)
- CloudWatch Logs write permissions (basic execution)

### 1.2 Worker Lambda role (rp-mw-worker)
Permissions should be limited to:
- `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` on inbound FIFO queue
- DynamoDB read/write to state tables
- `secretsmanager:GetSecretValue` for OpenAI/Richpanel/Shopify credentials
- CloudWatch Logs write
- (Optional) X-Ray write if enabled

### 1.3 “Deployment” role (CI/CD)
A separate role used by CI/CD to deploy infrastructure.
Avoid giving developers direct access to prod deploy actions.

---

## 2) Account + environment separation (required)
- prod, staging, dev in separate AWS accounts (Organizations)
- do not allow cross-account secret reads except via audited break-glass procedures

---

## 3) Policy patterns (required)
- Scope permissions to specific ARNs (queue ARN, table ARN, secret ARN)
- Use condition keys where practical:
  - restrict Secrets Manager access to `secretsmanager:ResourceTag/Environment = prod`
- Enable CloudTrail in all accounts (foundation)

---

## 4) Human access (recommended)
- Use IAM Identity Center (SSO) if possible
- Enforce MFA
- Use least-privilege groups (read-only, deployer, security admin)

---

## 5) Security review checklist for IAM changes
- No wildcard `*` on actions/resources unless justified
- No long-lived access keys for humans
- All roles have clear owners and rotation plans