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
npx cdk synth            # synthesizes all envs (dev/staging/prod)
# or only one env:
npx cdk synth -c env=dev
```

## Environments
Planned: `dev`, `staging`, `prod` (separate AWS accounts recommended).

Environment metadata (account, region, owner, tags) lives inside `cdk.json > context.environments`.

- Override per-run via `cdk synth -c env=dev` (also supports comma lists like `-c env=dev,staging`).
- Customize account IDs/regions/tags by editing `cdk.json` or supplying a `cdk.context.json` with the same shape.

> Secrets must come from AWS Secrets Manager. Do not put secrets in this repo.

## Naming helper
`lib/environments.ts` exposes `MwNaming`, which standardizes every namespace to `/rp-mw/<env>/...`.

- Secrets: `rp-mw/<env>/richpanel/api_key`
- SSM parameters: `/rp-mw/<env>/safe_mode`, `/rp-mw/<env>/automation_enabled`
- Lambda log groups: `/aws/lambda/rp-mw/<env>/<function>`

These match the paths documented in `docs/06_Security_Secrets/Access_and_Secrets_Inventory.md`
and `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`.

## Pre-provisioned config
Some foundations packs create SSM parameters and Secrets Manager placeholders ahead of CDK.

- The stack now *imports* `/rp-mw/<env>/safe_mode` and `/rp-mw/<env>/automation_enabled` instead of re-creating them, preventing `ParameterAlreadyExists` failures.
- Secrets such as `rp-mw/<env>/richpanel/api_key`, `.../richpanel/webhook_token`, and `.../openai/api_key` are referenced via `Secret.fromSecretNameV2`, so CDK can read them without owning their lifecycle.

## Status
This is a **scaffold**. Later waves will add actual resources incrementally.
