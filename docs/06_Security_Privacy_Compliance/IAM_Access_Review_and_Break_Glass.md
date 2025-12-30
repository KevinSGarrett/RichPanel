# IAM Access Review Cadence and Break-Glass Procedure (v1)

Last updated: 2025-12-22  
Applies to: AWS multi-account setup (`dev`, `staging`, `prod`)

This document defines:
- a **repeatable** IAM access review process (so permissions don’t drift)
- a controlled **break-glass** procedure for emergencies

Related:
- Least privilege design: `IAM_Least_Privilege.md`
- Incident response: `Incident_Response_Security_Runbooks.md`
- Monitoring baseline: `Security_Monitoring_Alarms_and_Dashboards.md`

---

## 1) IAM access review cadence (recommended)

### v1 cadence
- **Weekly (light):** review alerts, break-glass events, and any policy change PRs
- **Monthly (standard):** full access review for `prod`
- **Quarterly (deep):** least-privilege revalidation + policy tightening

### What “monthly review” includes (minimum)
- [ ] List all IAM users with access to `prod` (should be near zero; prefer SSO/roles)
- [ ] List all roles used by the middleware (`mw-ingress`, `mw-worker`, etc.)
- [ ] Confirm no one added wildcard permissions without a ticket/justification
- [ ] Review Secrets Manager access policy (who can read prod secrets)
- [ ] Review CloudTrail “AssumeRole” events for unusual principals
- [ ] Remove stale access (no recent use / left company / role changed)

### Tools and signals (recommended)
- IAM **Access Advisor** (last accessed)
- IAM **Access Analyzer** (external access / resource policies)
- CloudTrail queries for `AssumeRole`, `CreatePolicyVersion`, `PutRolePolicy`, etc.
- Config rules (optional) for detecting risky changes

---

## 2) Break-glass: purpose and constraints

### Purpose
Break-glass access exists to:
- restore service during an outage
- rotate secrets during compromise
- disable automation in an emergency
- unblock critical production incidents

### Constraints (v1)
- Break-glass should be **rare**
- Break-glass use must be **alarmed** (see monitoring doc)
- Break-glass sessions must be **time bounded**
- After usage, we do a short **post-incident review** and revert any temporary permissions

---

## 3) Recommended break-glass design (v1)

### Role name (example)
- `prod-breakglass-admin`

### Trust policy
- Trusted only by:
  - your primary admin identity (prefer AWS SSO or a dedicated IAM user with MFA)
  - optionally 1 backup owner (Leadership) for availability

### Permissions policy
- Start with `AdministratorAccess` (v1) **only if necessary**
- Prefer a reduced “emergency operator” policy if you can keep it small

### Session controls
- Require MFA
- Set maximum session duration (e.g., 1 hour)
- Disable long-lived access keys; prefer role assumption

### Alerting
- CloudTrail metric filter alarm on any `AssumeRole` into break-glass role (critical)

---

## 4) Break-glass use procedure (step-by-step)

1) **Declare incident** (even informally)
- [ ] Record a short note: why break-glass is needed, expected duration

2) **Assume break-glass role**
- [ ] Use MFA
- [ ] Confirm you are in the `prod` account and correct region (`us-east-2`)

3) **Perform minimal required actions**
Examples:
- rotate webhook token
- enable safe mode
- roll back a deployment
- fix IAM permissions preventing normal ops

4) **Exit and revoke**
- [ ] End session
- [ ] Revert any temporary changes (especially broad IAM grants)

5) **Post-incident review (required)**
- [ ] Add an entry in `Change_Log.md`
- [ ] Note what happened, what was changed, and why
- [ ] Add prevention action items (tighten policies/alarms/runbooks)

---

## 5) Minimum “IAM hygiene” rules (v1)
- No root access for day-to-day work (root is break-glass of last resort)
- MFA required for all console access
- Prefer role-based access (SSO) over IAM users + access keys
- No secrets committed to repos/docs
- Separate roles for ingress vs worker to limit blast radius

---

## 6) Owner
- Primary owner: **Developer (you)**
- Backup owner: **Leadership** (recommended)
