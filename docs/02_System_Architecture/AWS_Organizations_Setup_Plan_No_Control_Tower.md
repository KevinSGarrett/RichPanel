# AWS Organizations Setup Plan (No Control Tower)

Last updated: 2025-12-21

This document defines a **minimal, production-safe multi-account foundation** for this project **without** AWS Control Tower.

We are choosing this path because:
- you confirmed you **do not** have AWS Organizations / Control Tower set up yet
- we still want the **benefits of account isolation** (dev/staging/prod) without the overhead of a full landing zone product

Control Tower may still be adopted later, but it is **not required** to safely deploy this middleware.

---

## Target end-state (v1)

### Accounts
- **Management account** (a.k.a. payer / root org account)
  - used for: consolidated billing, account creation, org-wide policies
  - **do not deploy workloads here**
- **Workload accounts**
  - `dev`
  - `staging`
  - `prod`

Optional later (not required for v1):
- `log-archive`
- `audit/security`

### Region baseline
- Primary region: `us-east-2`
- Keep other regions disabled/unused by default unless explicitly needed.

---

## Recommended setup sequence (checklist)

### Step 0 — Decide who “owns” the AWS foundation

**Owner decision (confirmed):** You (developer) will own the AWS Organization management account.

Why we document this explicitly:
- the management account controls billing + account creation + org-wide security boundaries
- ownership ambiguity is a common cause of lockouts and delayed incident response

Before anything else, decide:
- who has access to the **root email inbox** for each AWS account
- who is responsible for **MFA devices**
- where we store the “break-glass” recovery instructions

> This is boring, but it prevents the most painful production outages: losing root access.

### Step 1 — Secure the first AWS account (future management account)
In the account that will become the organization management account:
1) Enable **root MFA**
2) Remove/avoid creating root access keys
3) Set **alternate contacts** (security/billing/operations)
4) Turn on IAM access to billing (so normal roles can view cost dashboards)

### Step 2 — Create AWS Organization
1) Create the AWS Organization
2) Enable “all features” mode (so SCPs are possible)

### Step 3 — Create an OU structure (minimal)
Minimal OU design:
- `Workloads`
  - `Dev`
  - `Staging`
  - `Prod`

If you want one extra OU for safety:
- `Sandbox`

### Step 4 — Create the 3 workload accounts
Create (or invite) the following accounts:
- `dev`
- `staging`
- `prod`

Account naming convention (recommended):
- Account name: `rp-mw-dev`, `rp-mw-staging`, `rp-mw-prod`
- Email alias pattern: `aws+rp-mw-dev@yourdomain.com` (or equivalent)

### Step 5 — Establish centralized access (SSO)
Best practice is to avoid long-lived IAM users.

Recommended:
- Enable **IAM Identity Center (SSO)**
- Create permission sets:
  - `ReadOnly`
  - `Developer`
  - `Deployer` (CI/CD role)
  - `BreakGlassAdmin` (very limited assignment)

### Step 6 — Baseline logging (minimum viable auditability)
At minimum we want:
- CloudTrail enabled (org-wide if possible)
- Logs stored in an S3 bucket with:
  - versioning
  - MFA delete (optional)
  - restricted write access

If we don’t create a separate `log-archive` account yet:
- store the CloudTrail logs in the management account, but with strict access controls

### Step 7 — Minimal guardrails (SCPs)
We will add a minimal set of Service Control Policies to reduce catastrophic mistakes.

Examples (high-level):
- deny disabling CloudTrail
- deny disabling Config (if enabled)
- deny leaving the organization
- deny deleting the log bucket

We will keep SCPs minimal to avoid developer friction.

### Step 8 — Cost guardrails (Budgets)
Set budgets early:
- monthly budget per account (especially `prod`)
- alerts to email/Slack

This prevents “surprise bills” during early iteration.

---

## Deployment implications for this project

Once accounts exist:
- IaC deploys the same stack into each account
- `prod` secrets and API keys are isolated
- DynamoDB/SQS separation prevents dev events from contaminating prod

We will document cross-account deploy roles and CI/CD in Wave 09.

---

## Acceptance criteria (done = true)

This setup step is considered complete when:
- AWS Organization exists
- `dev`, `staging`, `prod` accounts exist
- root MFA enabled in all accounts
- team access is via SSO/roles (not IAM users)
- baseline CloudTrail logging is active
- budgets are configured

---

## Risks & mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Root account compromise | catastrophic | root MFA + no root access keys + limited use |
| Losing root access | cannot recover | controlled root email inbox + documented recovery |
| Missing audit logs | hard to investigate incidents | org CloudTrail + protected S3 storage |
| Overly aggressive SCPs | blocks development | start minimal; expand later |
| No separation (single account) | dev mistakes impact prod | multi-account as early as possible |
