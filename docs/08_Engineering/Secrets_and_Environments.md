# Secrets and Environments

Last updated: 2026-01-27  
Status: Canonical

This document defines the **single source of truth** for secrets, environment configuration, and secret-to-environment mapping across all RichPanel Middleware environments (dev, staging, prod).

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Configuration](#environment-configuration)
3. [AWS Secrets Manager (Canonical)](#aws-secrets-manager-canonical)
4. [GitHub Actions Secrets](#github-actions-secrets)
5. [Environment Variable Overrides](#environment-variable-overrides)
6. [Security Constraints](#security-constraints)
7. [Code References](#code-references)
8. [Secret Rotation](#secret-rotation)

---

## Overview

**Philosophy:**
- **AWS Secrets Manager is the canonical source** for all runtime secrets in deployed environments (dev, staging, prod)
- **GitHub Actions Secrets** are used **only** for CI/PR smoke tests in dev (no Shopify sandbox/dev store exists)
- **Production secrets NEVER live in GitHub Actions Secrets**
- **Local development** uses environment variable overrides or local AWS profiles
  - **Shopify is live read-only in every environment**; do not create test orders.

**Naming convention:**
All secrets follow the pattern: `rp-mw/<env>/<integration>/<secret_type>`

Example: `rp-mw/dev/richpanel/api_key`

---

## Environment Configuration

### Supported Environments

| Environment | AWS Account    | Region     | Purpose                           |
|-------------|----------------|------------|-----------------------------------|
| `dev`       | 151124909266   | us-east-2  | Development + read-only validation |
| `staging`   | 260475105304   | us-east-2  | Pre-production read-only checks    |
| `prod`      | 878145708918   | us-east-2  | Live production (read-only mode)   |

**Environment resolution:**
The middleware resolves the active environment name from these variables (in order):
1. `RICHPANEL_ENV`
2. `RICH_PANEL_ENV`
3. `MW_ENV`
4. `ENV`
5. `ENVIRONMENT`
6. Default: `local`

**Note:** If `ENV` is set to `prod` in a non-prod environment, prod safety gates
will apply. Verify `ENV` is unset or explicitly non-prod in dev/sandbox stacks.

**Code reference:** `backend/src/richpanel_middleware/integrations/richpanel/client.py` L39-L49

---

## AWS Secrets Manager (Canonical)

All deployed Lambda functions load secrets from AWS Secrets Manager using the paths below.

### Production Secrets

| Environment | Integration | Secret Type            | AWS Secret Name/Path                      | Notes                                      |
|-------------|-------------|------------------------|-------------------------------------------|--------------------------------------------|
| **prod**    | Richpanel   | API key                | `rp-mw/prod/richpanel/api_key`            | **Read-only enforced by middleware code**  |
| **prod**    | Richpanel   | Webhook token          | `rp-mw/prod/richpanel/webhook_token`      | Ingress Lambda auth                        |
| **prod**    | Shopify     | Admin API token        | `rp-mw/prod/shopify/admin_api_token`      | **Must be read-only Admin API token**      |
| **prod**    | Shopify     | Client id              | `rp-mw/prod/shopify/client_id`            | OAuth refresh token support                |
| **prod**    | Shopify     | Client secret          | `rp-mw/prod/shopify/client_secret`        | OAuth refresh token support                |
| **prod**    | Shopify     | Refresh token          | `rp-mw/prod/shopify/refresh_token`        | Optional; required for rotating tokens     |
| **prod**    | OpenAI      | API key                | `rp-mw/prod/openai/api_key`               | Chat completion endpoint                   |

### Staging Secrets

| Environment | Integration | Secret Type            | AWS Secret Name/Path                      | Notes                                      |
|-------------|-------------|------------------------|-------------------------------------------|--------------------------------------------|
| **staging** | Richpanel   | API key                | `rp-mw/staging/richpanel/api_key`         | Staging Richpanel sandbox                  |
| **staging** | Richpanel   | Webhook token          | `rp-mw/staging/richpanel/webhook_token`   | Ingress Lambda auth                        |
| **staging** | Shopify     | Admin API token        | `rp-mw/staging/shopify/admin_api_token`   | Live store (read-only token)               |
| **staging** | Shopify     | Client id              | `rp-mw/staging/shopify/client_id`         | OAuth refresh token support                |
| **staging** | Shopify     | Client secret          | `rp-mw/staging/shopify/client_secret`     | OAuth refresh token support                |
| **staging** | Shopify     | Refresh token          | `rp-mw/staging/shopify/refresh_token`     | Optional; required for rotating tokens     |
| **staging** | OpenAI      | API key                | `rp-mw/staging/openai/api_key`            | Chat completion endpoint                   |

### Development Secrets

| Environment | Integration | Secret Type            | AWS Secret Name/Path                      | Notes                                      |
|-------------|-------------|------------------------|-------------------------------------------|--------------------------------------------|
| **dev**     | Richpanel   | API key                | `rp-mw/dev/richpanel/api_key`             | Dev sandbox (writes allowed)               |
| **dev**     | Richpanel   | Webhook token          | `rp-mw/dev/richpanel/webhook_token`       | Ingress Lambda auth                        |
| **dev**     | Shopify     | Admin API token        | `rp-mw/dev/shopify/admin_api_token`       | Live store (read-only token)               |
| **dev**     | Shopify     | Client id              | `rp-mw/dev/shopify/client_id`             | OAuth refresh token support                |
| **dev**     | Shopify     | Client secret          | `rp-mw/dev/shopify/client_secret`         | OAuth refresh token support                |
| **dev**     | Shopify     | Refresh token          | `rp-mw/dev/shopify/refresh_token`         | Optional; required for rotating tokens     |
| **dev**     | OpenAI      | API key                | `rp-mw/dev/openai/api_key`                | Chat completion endpoint                   |

### Shopify Legacy Path (Compatibility)

The Shopify client includes a **fallback** for a legacy secret path:
- **Canonical (preferred):** `rp-mw/<env>/shopify/admin_api_token`
- **Legacy (fallback):** `rp-mw/<env>/shopify/access_token`

The client tries the canonical path first, then falls back to the legacy path if not found.

**Important:** There is **no Shopify sandbox/dev store**. All environments use the **same live store**
with **read-only** tokens, so avoid writing or testing write scopes and **do not create test orders**.

The admin API token secret can be either a plain token string or a JSON payload:

```json
{
  "access_token": "<token>",
  "refresh_token": "<refresh>",
  "expires_at": 1735689600
}
```

For rotating tokens, the refresh Lambda uses the Shopify OAuth
`grant_type=refresh_token` flow with the client id/secret **and a refresh
token** to mint a fresh access token on a schedule. If no refresh token is
available, the refresh job **skips** rotation and leaves the stable admin API
token intact.

**Code reference:** `backend/src/integrations/shopify/client.py` L178-L189

---

## GitHub Actions Secrets

GitHub Actions Secrets are used **exclusively** for CI/PR smoke tests in dev. They are **NOT** used for staging or production deployments, and Shopify credentials remain in AWS Secrets Manager only (live read-only store).

### Current GitHub Secrets (Repository Settings → Secrets and Variables → Actions)

| Secret Name                     | Purpose                                          | Maps to AWS Secret Path              |
|---------------------------------|--------------------------------------------------|--------------------------------------|
| `DEV_RICHPANEL_API_KEY`         | Dev sandbox Richpanel API key (CI smoke tests)   | `rp-mw/dev/richpanel/api_key`        |
| `DEV_RICHPANEL_WEBHOOK_TOKEN`   | Dev sandbox Richpanel webhook token (CI ingress) | `rp-mw/dev/richpanel/webhook_token`  |
| `DEV_OPENAI_API_KEY`            | Dev OpenAI API key (optional CI tests)           | `rp-mw/dev/openai/api_key`           |
| `STAGING_RICHPANEL_API_KEY`     | Staging Richpanel API key (optional CI tests)    | `rp-mw/staging/richpanel/api_key`    |
| `STAGING_RICHPANEL_WEBHOOK_TOKEN` | Staging webhook token (optional CI tests)      | `rp-mw/staging/richpanel/webhook_token` |
| `STAGING_OPENAI_API_KEY`        | Staging OpenAI API key (optional CI tests)       | `rp-mw/staging/openai/api_key`       |
| `CODECOV_TOKEN`                 | Codecov upload token (coverage reporting)        | N/A (Codecov service)                |

**Shopify token strategy for CI:** production workflows fetch
`rp-mw/prod/shopify/admin_api_token` via GitHub OIDC + AWS Secrets Manager
(`order_status_prod_shadow.yml`, `shadow_live_readonly_eval.yml`). This keeps
Shopify tokens in AWS as the single source of truth and avoids rotating tokens
in GitHub secrets.

### ⚠️ Production Secret Policy

**DO NOT store production secrets in GitHub Actions Secrets.**

If CI/CD workflows need to interact with production:
- **Preferred:** Use GitHub OIDC → AWS IAM role assumption to read secrets from AWS Secrets Manager at runtime
- **Alternative:** Use GitHub Environments with manual approval gates
- **Never:** Copy production secret values into GitHub repository secrets

**Code reference (ingress webhook token wiring):** `infra/cdk/lib/richpanel-middleware-stack.ts` L233-L238

**Code reference (worker secret wiring):** `infra/cdk/lib/richpanel-middleware-stack.ts` L267-L270

---

## Environment Variable Overrides

All integration clients support **environment variable overrides** for local development and testing without AWS credentials.

### Richpanel Client Overrides

| Environment Variable                 | Purpose                                      | Default Behavior                        |
|--------------------------------------|----------------------------------------------|-----------------------------------------|
| `RICHPANEL_API_KEY_OVERRIDE`         | Override API key (skip Secrets Manager)      | Uses AWS Secrets Manager if not set     |
| `RICHPANEL_API_KEY_SECRET_ARN`       | Custom secret path                           | `rp-mw/<env>/richpanel/api_key`         |
| `RICHPANEL_OUTBOUND_ENABLED`         | Enable outbound writes (default: dry-run)    | `false` (dry-run by default)            |
| `MW_OUTBOUND_ALLOWLIST_EMAILS`       | Allowlist full customer emails               | Empty (no allowlist by default)         |
| `MW_OUTBOUND_ALLOWLIST_DOMAINS`      | Allowlist customer email domains             | Empty (no allowlist by default)         |
| `RICHPANEL_WRITE_DISABLED`           | Hard block all non-GET/HEAD requests         | `false` (write block off by default)    |
| `RICHPANEL_READ_ONLY`                | Force GET/HEAD-only requests                 | `false` (read-only off by default)      |
| `RICHPANEL_HTTP_MAX_ATTEMPTS`        | Max retry attempts for Richpanel HTTP calls  | `3`                                     |
| `RICHPANEL_429_COOLDOWN_MULTIPLIER`  | Extra cooldown applied after 429 retries     | `1.0`                                   |
| `RICHPANEL_TOKEN_POOL_ENABLED`       | Enable optional token pool rotation          | `false`                                 |
| `RICHPANEL_TOKEN_POOL_SECRET_IDS`    | Comma-delimited secret ids for token pool    | empty                                  |

**Code reference (secret path resolution):** `backend/src/richpanel_middleware/integrations/richpanel/client.py` L217-L221

**Code reference (write blocking):** `backend/src/richpanel_middleware/integrations/richpanel/client.py` L255-L264, L542-L544

### Shopify Client Overrides

| Environment Variable                 | Purpose                                      | Default Behavior                        |
|--------------------------------------|----------------------------------------------|-----------------------------------------|
| `SHOPIFY_ACCESS_TOKEN_OVERRIDE`      | Override access token (skip Secrets Manager) | Uses AWS Secrets Manager if not set     |
| `SHOPIFY_ACCESS_TOKEN_SECRET_ID`     | Custom secret path                           | `rp-mw/<env>/shopify/admin_api_token`   |
| `SHOPIFY_CLIENT_ID_OVERRIDE`         | Override Shopify client id                   | Uses AWS Secrets Manager if not set     |
| `SHOPIFY_CLIENT_SECRET_OVERRIDE`     | Override Shopify client secret               | Uses AWS Secrets Manager if not set     |
| `SHOPIFY_CLIENT_ID_SECRET_ID`        | Custom client id secret path                 | `rp-mw/<env>/shopify/client_id`         |
| `SHOPIFY_CLIENT_SECRET_SECRET_ID`    | Custom client secret path                    | `rp-mw/<env>/shopify/client_secret`     |
| `SHOPIFY_REFRESH_TOKEN_SECRET_ID`    | Custom refresh token path                    | `rp-mw/<env>/shopify/refresh_token`     |
| `SHOPIFY_REFRESH_TOKEN_OVERRIDE`     | Override refresh token (skip Secrets Manager) | Uses AWS Secrets Manager if not set    |
| `SHOPIFY_OUTBOUND_ENABLED`           | Enable network calls (default: offline)      | `false` (offline by default)            |
| `SHOPIFY_SHOP_DOMAIN`                | Shopify shop domain                          | `example.myshopify.com`                 |

**Code reference (secret path + fallback):** `backend/src/integrations/shopify/client.py` L178-L189

### OpenAI Client Overrides

| Environment Variable                 | Purpose                                      | Default Behavior                        |
|--------------------------------------|----------------------------------------------|-----------------------------------------|
| `OPENAI_API_KEY`                     | Override API key (skip Secrets Manager)      | Uses AWS Secrets Manager if not set     |
| `OPENAI_API_KEY_SECRET_ID`           | Custom secret path                           | `rp-mw/<env>/openai/api_key`            |
| `OPENAI_ALLOW_NETWORK`               | Enable network calls (default: offline)      | `false` (offline by default)            |

**Code reference (secret path):** `backend/src/integrations/openai/client.py` L191-L195

### Outbound & Write Safety Registry (Canonical)

This registry lists environment variables that influence outbound behavior or write safety. Safe defaults are the recommended baseline for each environment; "unset" means not present in the Lambda config.

| Environment Variable | Purpose | Safe default (dev / staging / prod) | Danger level |
|---|---|---|---|
| `RICHPANEL_OUTBOUND_ENABLED` | Enable Richpanel outbound writes and customer replies | `false / false / false` | High |
| `MW_ALLOW_NETWORK_READS` | Allow read-only network calls when outbound is disabled | `false / false / false` | Medium |
| `MW_OUTBOUND_ALLOWLIST_EMAILS` | Allowlist customer emails for email-channel replies | `empty / empty / empty` | High |
| `MW_OUTBOUND_ALLOWLIST_DOMAINS` | Allowlist customer email domains | `empty / empty / empty` | High |
| `RICHPANEL_BOT_AGENT_ID` | Bot agent id for email-channel replies (preferred) | `empty / empty / empty` | High |
| `RICHPANEL_BOT_AUTHOR_ID` | Bot author id for email-channel replies (legacy fallback) | `empty / empty / empty` | High |
| `MW_PROD_WRITES_ACK` | Prod-only write acknowledgment gate | `unset / unset / unset` | Critical |
| `RICHPANEL_READ_ONLY` (or `RICH_PANEL_READ_ONLY`) | Force GET/HEAD-only requests | `false / true / true` (effective default via env) | High |
| `RICHPANEL_WRITE_DISABLED` | Hard block all non-GET/HEAD requests | `false / false / false` | Low |
| `SHOPIFY_OUTBOUND_ENABLED` | Enable Shopify network calls | `false / false / false` | Medium |
| `OPENAI_ALLOW_NETWORK` | Enable OpenAI network calls | `false / false / false` | Medium |
| `SHIPSTATION_OUTBOUND_ENABLED` | Enable ShipStation network calls | `false / false / false` | Medium |

Danger level legend: Low = safety-only; Medium = enables read-only network calls; High = enables or restricts customer-facing outbound; Critical = unlocks prod writes.

Deployment source: `MW_OUTBOUND_ALLOWLIST_*`, `RICHPANEL_BOT_AGENT_ID`, and `RICHPANEL_BOT_AUTHOR_ID` are wired into the worker Lambda via CDK. Set per-environment values in `infra/cdk/cdk.json` under `context.environments.<env>` as `outboundAllowlistEmails`, `outboundAllowlistDomains`, and `richpanelBotAuthorId` (or override via `cdk.context.json`).

#### Gate behavior summary
- Writes gate: `MW_PROD_WRITES_ACK` must be acknowledged for prod writes; `RICHPANEL_READ_ONLY` and `RICHPANEL_WRITE_DISABLED` force read-only regardless.
- Outbound on/off: `RICHPANEL_OUTBOUND_ENABLED` controls Richpanel outbound writes and customer replies (default off).
- Outbound restriction: `MW_OUTBOUND_ALLOWLIST_EMAILS` and `MW_OUTBOUND_ALLOWLIST_DOMAINS` must include the customer for email replies.
- Bot identity: `RICHPANEL_BOT_AGENT_ID` (or fallback `RICHPANEL_BOT_AUTHOR_ID`) is required for email-channel replies in prod; missing value blocks outbound.
- Network reads: `MW_ALLOW_NETWORK_READS` allows read-only network calls when outbound is disabled.
- Vendor network toggles: `SHOPIFY_OUTBOUND_ENABLED`, `OPENAI_ALLOW_NETWORK`, `SHIPSTATION_OUTBOUND_ENABLED` control external network calls for their integrations.
- Environment resolution (`RICHPANEL_ENV` / `RICH_PANEL_ENV` / `MW_ENV` / `ENV` / `ENVIRONMENT`) determines prod safety gates; see Environment Configuration.

#### Quick rollback (prod-safe)
1. Set `RICHPANEL_OUTBOUND_ENABLED=false` (or unset).
2. Unset `MW_PROD_WRITES_ACK`.
3. Optional: set `RICHPANEL_WRITE_DISABLED=true` for an immediate hard block.

#### Deployed config lint (PII-safe)
Run:
```bash
python scripts/lint_middleware_lambda_config.py --env prod --region us-east-2
```

Sample output:
```
Environment: prod
Function: rp-mw-prod-worker
Outbound enabled: false
Prod writes ACK acknowledged: false
Allowlist emails: 0
Allowlist domains: 0
Bot agent id set: false
Bot author id set: false
```

---

## Security Constraints

### Richpanel Production Safety

**Problem:** Richpanel API keys **cannot be scoped read-only** at the API level.

**Solution:** The middleware enforces **read-only "shadow mode"** in production via code-level write blocking:

1. **Environment-based enforcement:** The Richpanel client defaults to read-only for `staging`/`prod` (`READ_ONLY_ENVIRONMENTS`) unless explicitly overridden by `RICHPANEL_READ_ONLY`.
2. **Request-level blocking:** The `RichpanelClient.request()` method checks for read-only or write-disabled mode; only `GET`/`HEAD` are allowed and all other methods (`POST`, `PUT`, `PATCH`, `DELETE`) raise `RichpanelWriteDisabledError` before the network call.
3. **Optional hard block:** `RICHPANEL_WRITE_DISABLED=true` forces read-only regardless of environment.
4. **Safety gates:** Worker logic checks `safe_mode` and `automation_enabled` SSM parameters before executing any automation.

**Code reference (write gate):** `backend/src/richpanel_middleware/integrations/richpanel/client.py` L255-L264

**Code reference (write disabled static check):** `backend/src/richpanel_middleware/integrations/richpanel/client.py` L542-L544

### Shopify Production Safety

**Requirement:** The Shopify Admin API token **must be a read-only scoped token**.

**Recommended scopes:**
- `read_orders`
- `read_customers` (if needed)
- `read_fulfillments`

**DO NOT grant:**
- `write_orders`
- `write_customers`
- `write_fulfillments`

The middleware uses the Shopify client exclusively for **order lookups** in production. All order data is read-only.

---

## Code References

### Secret Path Naming Convention

**File:** `infra/cdk/lib/environments.ts`  
**Lines:** 108-126  
**Class:** `MwNaming`  
**Method:** `secretPath(...segments: string[]): string`

```typescript
secretPath(...segments: string[]): string {
  return [this.namespace(false), ...segments.map(sanitizeSegment)].join("/");
}
```

**Example usage:**
```typescript
this.naming.secretPath("richpanel", "api_key")
// Returns: "rp-mw/dev/richpanel/api_key" (when env=dev)
```

### Richpanel Client Secret Loading

**File:** `backend/src/richpanel_middleware/integrations/richpanel/client.py`  
**Lines:** 185-238 (constructor), 433-460 (secret loading)

The client resolves the secret path from:
1. Constructor parameter `api_key_secret_id`
2. Environment variable `RICHPANEL_API_KEY_SECRET_ARN`
3. Environment variable `RICHPANEL_API_KEY_SECRET_ID`
4. Default: `rp-mw/{environment}/richpanel/api_key`

### Webhook Token Loading (Ingress Lambda)

**File:** `backend/src/lambda_handlers/ingress/handler.py`  
**Lines:** 24-110

The ingress Lambda reads the webhook token from the environment variable `WEBHOOK_SECRET_ARN` (set by CDK to `rp-mw/<env>/richpanel/webhook_token`) and caches it for 300 seconds (default TTL).

### CDK Secret Wiring

**File:** `infra/cdk/lib/richpanel-middleware-stack.ts`  
**Lines:** 103-121 (secret imports), 233-238 (ingress env), 267-270 (worker env)

The CDK stack imports secret references using `Secret.fromSecretNameV2()` and passes them as environment variables to Lambda functions.

### Secrets Manager Policy

**File:** `infra/cdk/README.md`  
**Lines:** 31-38, 47

Example naming convention and policy references.

---

## Secret Rotation

### Rotation Policy

- **Richpanel sandbox (dev):** Rotate every 90 days or when leaked
- **Richpanel production:** Rotate every 60 days
- **Shopify Admin API tokens:** Rotate every 90 days
- **OpenAI API keys:** Rotate every 90 days or when leaked
- **Webhook tokens:** Rotate every 90 days or immediately if exposed in logs/commits

### Rotation Procedure

1. **Generate new secret value** (in the source system: Richpanel, Shopify, OpenAI)
2. **Update AWS Secrets Manager** via console or CLI:
   ```bash
   aws secretsmanager update-secret \
     --secret-id rp-mw/<env>/<integration>/<secret_type> \
     --secret-string "<NEW_VALUE>" \
     --region us-east-2
   ```
3. **Test the new secret** by running a smoke test (dev/staging)
4. **Invalidate old secret** in the source system (Richpanel, Shopify, OpenAI)
5. **Document rotation** in `docs/00_Project_Admin/Change_Log.md`

### GitHub Actions Secret Rotation

If a GitHub Actions secret is rotated (e.g., `DEV_RICHPANEL_API_KEY`):
1. Update the secret in **GitHub repository settings** (Settings → Secrets and variables → Actions)
2. Trigger a CI run to validate the new secret
3. Update corresponding AWS Secrets Manager entry if both are in sync

---

## Related Documentation

- **CI and Actions Runbook:** `docs/08_Engineering/CI_and_Actions_Runbook.md`
- **Access and Secrets Inventory:** `docs/06_Security_Secrets/Access_and_Secrets_Inventory.md`
- **Parameter Defaults:** `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- **CDK Infrastructure:** `infra/cdk/README.md`
- **Prod Read-Only Shadow Mode:** `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`

---

## Appendix: Quick Reference Tables

### Environment → AWS Account Mapping

| Environment | AWS Account ID | Purpose                  |
|-------------|----------------|--------------------------|
| dev         | 151124909266   | Sandbox + dev testing    |
| staging     | 260475105304   | Pre-production validation|
| prod        | 878145708918   | Live production          |

### Secret Path Templates

| Integration | Secret Type        | Path Template                                |
|-------------|--------------------|----------------------------------------------|
| Richpanel   | API key            | `rp-mw/<env>/richpanel/api_key`              |
| Richpanel   | Webhook token      | `rp-mw/<env>/richpanel/webhook_token`        |
| Shopify     | Admin API token    | `rp-mw/<env>/shopify/admin_api_token`        |
| OpenAI      | API key            | `rp-mw/<env>/openai/api_key`                 |

---

**End of Document**
