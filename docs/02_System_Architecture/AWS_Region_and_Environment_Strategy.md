# AWS Region and Environment Strategy

Last updated: 2025-12-21

This document captures our **default** AWS region selection and environment/account strategy for the Richpanel middleware.
It is optimized for:
- US-wide customer base (latency)
- production isolation (security + blast radius)
- simplicity for early rollout, with a clean path to hardening

---

## 1) Region selection criteria (what matters)

When choosing a primary AWS region, we balance:
1) **Latency to users and third-party APIs**
   - Customers are across the United States.
   - We also depend on SaaS APIs (Richpanel, Shopify, OpenAI). Their hosting region is not fully controllable.
2) **Service availability**
   - We require: API Gateway, Lambda, SQS, DynamoDB, Secrets Manager, CloudWatch.
3) **Operational simplicity**
   - Single region initially; multi-region later if needed.
4) **Resilience**
   - Multi-AZ within region for v1.
   - Multi-region disaster recovery as a future hardening step.

---

## 2) Selected primary region (v1)

**Primary region (recommended):** `us-east-2` (US East — Ohio)

Why this region is a good default for this project:
- It is **geographically more central** than `us-east-1` and typically yields a more balanced latency profile across the US.
- It is a standard (non–opt-in) region and supports the AWS services required for the recommended serverless stack.

> If you already have existing AWS infrastructure/accounts in another region, we should strongly consider colocating with that region to reduce complexity.

---

## 3) Secondary region (future DR option)

**Secondary/DR region (optional, later):** `us-west-2` (US West — Oregon)

Use cases:
- business requires continued operation during a region-level incident
- leadership decides uptime requirements justify multi-region complexity/cost

Recommended DR posture for this project:
- Start with **documented DR runbook** (manual failover) before implementing full active/active.
- Keep the architecture “multi-region ready” by avoiding region-locked assumptions (hardcoded ARNs, etc.)

---

## 4) Environment and account strategy (recommended)

### 4.1 Default recommendation (best practice)
Use **AWS Organizations** (or **AWS Control Tower**) with separate AWS accounts:

- **`dev` account** — development, feature testing, sandboxes
- **`staging` account** — pre-prod validation, mirrors prod config
- **`prod` account** — production only

Optional (Control Tower standard pattern):
- **`log-archive` account** — centralized immutable logs
- **`audit/security` account** — security tooling, delegated admin

Why multi-account:
- production isolation (blast radius reduction)
- simpler least-privilege IAM
- clearer budget controls + cost attribution
- fewer “oops” incidents from dev resources affecting prod

### 4.2 Minimal fallback (if we must keep it very simple)
If spinning up multiple accounts is too heavy initially:
- **2 accounts**: `prod` + `nonprod` (dev/stage combined)
- Still enforce strict IAM boundaries and separate data stores.

### 4.3 Current state + recommended setup path (no Organizations/Control Tower yet)
You confirmed you **do not currently have** AWS Organizations / Control Tower set up.

That does **not** block documentation or local development, but it **does** impact how we safely deploy environments.

**Best-suggested path (recommended):**
1) Create an **AWS Organization** (without Control Tower for now).
2) Create 3 workload accounts inside it: `dev`, `staging`, `prod`.
3) Add a minimal “landing zone” baseline:
   - root MFA + alternate contacts
   - centralized audit logging (CloudTrail org trail)
   - minimal Service Control Policies (SCPs) to prevent disabling logging
   - budget alarms

**Why not Control Tower immediately?**
- Control Tower is great, but it introduces additional moving parts.
- For an early rollout, an Organizations-only landing zone gets us the isolation we need with less operational overhead.

We document the step-by-step plan here:
- `AWS_Organizations_Setup_Plan_No_Control_Tower.md`

---

## 5) CI/CD deployment model (high-level)

We will document full CI/CD later (Wave 09), but our default model is:

- Infrastructure-as-Code (Terraform/CDK) defines all resources per environment.
- A CI system assumes a cross-account role into each environment account.
- Deploy flow:
  - PR → dev
  - Release candidate → staging
  - Approved release → prod

---

## 6) Notes / open confirmations

- ✅ AWS Organizations / Control Tower are **not** currently set up (confirmed).
- Confirm whether any compliance/data residency constraints apply beyond “US only”.
