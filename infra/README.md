# Infra (IaC)

**Primary IaC tool (v1):** **AWS CDK (TypeScript)** → `infra/cdk/`

Target architecture:
- API Gateway → ingress Lambda (ACK-fast)
- SQS FIFO (+ DLQ)
- worker Lambda(s)
- DynamoDB (idempotency + minimal state)
- alarms + dashboards

References:
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

## Layout
- `cdk/` — **primary**
- `terraform/` — optional future alternative (not used in v1)
- `sam/` — optional future alternative (not used in v1)

### CDK multi-env scaffold
- `infra/cdk` now materializes `dev`, `staging`, `prod` stacks from a single entrypoint.
- Environment metadata (account/region/tags) is stored in `infra/cdk/cdk.json` and can be overridden via `-c env=<name>`.
- Naming + parameters are centralized in `lib/environments.ts` to enforce `/rp-mw/<env>/...` prefixes for secrets, SSM parameters, logs, and metrics.

## Rule
Pick **one** IaC tool for implementation to avoid drift. For this repo: CDK is canonical.
