# W12-EP01-T011 — Create IAM roles and least-privilege policies for middleware (ingress vs worker) and CI deploy

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra

## Objective
Ensure the middleware runs with strict least privilege and deploy pipeline has minimal rights.

## Context / References
- `docs/06_Security_Privacy_Compliance/IAM_Least_Privilege.md`
- `docs/06_Security_Privacy_Compliance/IAM_Access_Review_and_Break_Glass.md`

## Dependencies
- W12-EP01-T010

## Implementation steps
1. Create separate execution roles: `mw-ingress`, `mw-worker` with minimal permissions (SQS, DynamoDB, CloudWatch, SSM, Secrets).
1. Create deploy role for CI/CD with permission boundaries.
1. Set up break-glass role with MFA requirement and alerting.
1. Document role ARNs and responsibilities.

## Acceptance criteria
- [ ] Roles created with permission boundaries.
- [ ] Ingress role cannot perform worker-only actions (principle of least privilege).
- [ ] Break-glass role exists and alerts are configured.

## Test plan
- Manual: attempt prohibited action from ingress role and confirm denied.
- Manual: CloudTrail shows role assumptions.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Enable short session durations.
- Enable alerts on break-glass role assumption.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
