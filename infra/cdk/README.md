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
Wave B2 delivers the first end-to-end pipeline that we can deploy in dev/staging:

- HTTP API Gateway endpoint (`POST /webhook`) with Lambda proxy integration.
- Ingress Lambda (`rp-mw-<env>-ingress`) that validates the Richpanel webhook token from Secrets Manager and enqueues events onto a FIFO queue.
- SQS FIFO queue (`rp-mw-<env>-events.fifo`) backed by a FIFO DLQ.
- Worker Lambda (`rp-mw-<env>-worker`) subscribed to the queue. It logs every event, enforces `/rp-mw/<env>/safe_mode` and `/rp-mw/<env>/automation_enabled`, and writes idempotency records.
- DynamoDB table (`rp_mw_<env>_idempotency`) that stores the worker’s idempotency state.

Later waves will extend the worker logic, add observability/alarms, and introduce downstream integrations.

## CloudFormation outputs
Synth/deploy now emits helper outputs:

- `IngressEndpointUrl` — HTTP API invoke URL (public).
- `EventsQueueName` / `EventsQueueUrl` — FIFO queue identifiers for smoke tests and emergency tooling.
- Existing naming outputs (`NamespacePrefix`, `SafeModeParamPath`, etc.) remain unchanged.

## Local smoke test
`python scripts/test_pipeline_handlers.py` exercises both Lambda handlers with stubbed AWS clients.  
This script runs automatically via `python scripts/run_ci_checks.py` and in GitHub Actions, so keep it green when making changes.
