# W12-EP01-T010 — Set up AWS Organization and create dev/staging/prod accounts (Organizations-only)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra

## Objective
Create secure AWS account boundaries for environments without Control Tower.

## Context / References
- `docs/02_System_Architecture/AWS_Organizations_Setup_Plan_No_Control_Tower.md`
- `docs/06_Security_Privacy_Compliance/AWS_Security_Baseline_Checklist.md`

## Dependencies
- W12-EP00-T001

## Implementation steps
1. Create AWS Organization (management account owned by developer per decision).
1. Create workload accounts: dev, staging, prod (or document minimal fallback).
1. Enable MFA on root accounts; set alternate contacts.
1. Enable consolidated billing and budgets/alerts per account.
1. Document account IDs in a secure out-of-band place; store only non-sensitive references in docs.

## Acceptance criteria
- [ ] Accounts created and accessible.
- [ ] Budgets and root MFA enabled.
- [ ] Baseline checklist items for account setup checked.

## Test plan
- Manual: assume role into each account and confirm least-privilege permissions.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- No root access for daily work; use IAM roles only.
- Break-glass procedure documented.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
