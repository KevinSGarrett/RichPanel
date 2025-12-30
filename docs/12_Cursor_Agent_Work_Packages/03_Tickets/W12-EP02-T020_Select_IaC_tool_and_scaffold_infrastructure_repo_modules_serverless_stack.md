# W12-EP02-T020 — Select IaC tool and scaffold infrastructure repo modules (serverless stack)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra

## Objective
Create reproducible deployments for API Gateway, Lambdas, SQS, DynamoDB, alarms.

## Context / References
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

## Dependencies
- W12-EP01-T010

## Implementation steps
1. Choose IaC approach (recommended: AWS CDK; acceptable: Terraform). Record decision.
1. Scaffold project structure with environment-specific stacks.
1. Implement baseline resources with tags and naming conventions.
1. Wire IaC outputs needed by app (queue URL, table names, API URL).

## Acceptance criteria
- [ ] IaC can deploy dev environment end-to-end.
- [ ] Environment separation supported (stack names or accounts).
- [ ] Outputs documented.

## Test plan
- Deploy and destroy dev stack successfully.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
