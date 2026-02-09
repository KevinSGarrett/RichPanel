# AWS Account Resource Map

Last updated: 2026-02-08  
Status: Canonical

## Account → Environment Map

| Environment | AWS Account ID | Region | Stack Name |
| --- | --- | --- | --- |
| dev | 151124909266 | us-east-2 | RichpanelMiddleware-dev |
| prod | 878145708918 | us-east-2 | RichpanelMiddleware-prod |

## API Gateway + Lambda Ownership

### DEV (account 151124909266)
- API Gateway (HTTP API): `rp-mw-dev-ingress` (API ID `pj41mkbj38`)
- Lambda (ingress): `rp-mw-dev-ingress`
- Lambda (worker): `rp-mw-dev-worker`
- Lambda (Shopify refresh): `rp-mw-dev-shopify-token-refresh`

### PROD (account 878145708918)
- API Gateway (HTTP API): `rp-mw-prod-ingress` (API ID from `IngressEndpointUrl` output in `RichpanelMiddleware-prod`)
- Lambda (ingress): `rp-mw-prod-ingress`
- Lambda (worker): `rp-mw-prod-worker`
- Lambda (Shopify refresh): `rp-mw-prod-shopify-token-refresh`

## Secrets Manager Paths (Authoritative)

### DEV (account 151124909266)
- `rp-mw/dev/shopify/admin_api_token`
- `rp-mw/dev/shopify/client_id`
- `rp-mw/dev/shopify/client_secret`
- `rp-mw/dev/shopify/refresh_token`

### PROD (account 878145708918)
- `rp-mw/prod/shopify/admin_api_token`
- `rp-mw/prod/shopify/client_id`
- `rp-mw/prod/shopify/client_secret`
- `rp-mw/prod/shopify/refresh_token`

## Cursor AWS Profiles

Typical SSO profile names used in runs:
- DEV: `rp-admin-dev-admin`
- PROD: `rp-admin-prod`

Set via `AWS_PROFILE` or `--profile/--aws-profile` in scripts. Verify available profiles with
`aws configure list-profiles` and use the one that maps to the target account.

## How to Verify

### Confirm account + region
```bash
aws sts get-caller-identity --profile rp-admin-dev-admin
aws sts get-caller-identity --profile rp-admin-prod
```

### Confirm API Gateway + stack outputs
```bash
aws cloudformation describe-stacks \
  --stack-name RichpanelMiddleware-dev \
  --region us-east-2 \
  --query "Stacks[0].Outputs"

aws cloudformation describe-stacks \
  --stack-name RichpanelMiddleware-prod \
  --region us-east-2 \
  --query "Stacks[0].Outputs"
```

### Confirm API Gateway name → ID mapping
```bash
aws apigatewayv2 get-apis \
  --region us-east-2 \
  --query "Items[?Name=='rp-mw-dev-ingress'].[Name,ApiId]"

aws apigatewayv2 get-apis \
  --region us-east-2 \
  --query "Items[?Name=='rp-mw-prod-ingress'].[Name,ApiId]"
```

### Confirm Lambda ownership
```bash
aws lambda list-functions \
  --region us-east-2 \
  --query "Functions[?starts_with(FunctionName,'rp-mw-dev-')].[FunctionName,Runtime]"

aws lambda list-functions \
  --region us-east-2 \
  --query "Functions[?starts_with(FunctionName,'rp-mw-prod-')].[FunctionName,Runtime]"
```

### Confirm Secrets Manager paths
```bash
aws secretsmanager describe-secret --secret-id rp-mw/dev/shopify/admin_api_token --region us-east-2
aws secretsmanager describe-secret --secret-id rp-mw/prod/shopify/admin_api_token --region us-east-2
```
