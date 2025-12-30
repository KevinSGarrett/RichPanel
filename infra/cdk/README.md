# Infra — AWS CDK (TypeScript)

This is the **primary IaC tool of record** for v1.

Target architecture:
- API Gateway → ingress Lambda (ACK-fast) → SQS FIFO (+DLQ) → worker Lambdas → DynamoDB (idempotency/state)
- Observability + alarms

References:
- `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

## Quick start (local)
```bash
cd infra/cdk
npm install
npm run build
npx cdk synth
```

## Environments
Planned: `dev`, `staging`, `prod` (separate AWS accounts recommended).

> Secrets must come from AWS Secrets Manager. Do not put secrets in this repo.

## Status
This is a **scaffold**. Later waves will add actual resources incrementally.
