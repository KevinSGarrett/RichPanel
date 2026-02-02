# Access & Secrets Inventory (Sprint 0)

Last updated: 2026-01-04  
Owners: Security & Platform (Agent 2) / Eng Lead

> Scope: capture the minimum external access required to unblock Build Mode Stream B1 (“Sprint 0 preflight”) before infrastructure work proceeds. Source: [Active workstreams](../REHYDRATION_PACK/03_ACTIVE_WORKSTREAMS.md#stream-b1--sprint-0-preflight-access--secrets-inventory).

---

## 1) Quick status snapshot

| Access / Secret | Why we need it | Environments | Storage / location | Status & owner |
| --- | --- | --- | --- | --- |
| AWS accounts + GitHub OIDC deploy role | Host middleware in separate accounts per [AWS serverless reference](../02_System_Architecture/AWS_Serverless_Reference_Architecture.md) and enforce least privilege ([IAM design](../06_Security_Privacy_Compliance/IAM_Least_Privilege.md)). | `dev`, `staging`, `prod` (separate accounts + `us-east-2` region) | AWS accounts (below), GitHub Actions OIDC provider (`token.actions.githubusercontent.com`), deploy role: `rp-ci-deploy` (assumed by `.github/workflows/deploy-*.yml` + `*-e2e-smoke.yml`). | Owner: Engineering (Kevin). **Status:** accounts created + OIDC deploy role active. |
| Richpanel API key (`x-richpanel-key`) | Server-to-server reads/writes and reconciliation sweeps per [webhook + API plan](../03_Richpanel_Integration/Webhooks_and_Event_Handling.md). | Unique per env (staging may share prod workspace per [env strategy](../09_Deployment_Operations/Environments.md#richpanel-environment-strategy)). | AWS Secrets Manager `rp-mw/<env>/richpanel/api_key`. Inject at deploy via Lambda env vars. | Owner: CX Ops / Workspace admin. **Pending:** need tenant admin to mint non-prod + prod keys. |
| Richpanel webhook token (`X-Middleware-Token`) | Validates inbound `POST /richpanel/inbound` requests (shared-secret header, per webhook doc §4.1/§6.1). | Unique per env (dev/staging tokens can live in sandbox workspace). | Secrets Manager `rp-mw/<env>/richpanel/webhook_token` + configured inside Richpanel HTTP Target. | Owner: Integration + CX Ops. **Pending:** HTTP Target not created yet; token must exist before enabling trigger. |
| OpenAI API key | LLM routing + FAQ automation (per [OpenAI env strategy](../09_Deployment_Operations/Environments.md#openai-environment-strategy)). | Unique per env; dev/staging use low-quota keys; prod isolated. | Secrets Manager `rp-mw/<env>/openai/api_key`. | Owner: Product/Leadership. **Pending:** request procurement + budget caps. |
| Shopify Admin API token | Commerce reads (order lookup + reconciliation) when Shopify is the system of record. | Prod required; staging optional; dev uses stubs/mocks. | Secrets Manager (canonical): `rp-mw/<env>/shopify/admin_api_token` (legacy fallback: `rp-mw/<env>/shopify/access_token`). | Owner: Ops / Ecom admin. **Pending:** confirm store(s) + mint token (least scope). |
| ShipStation credential set | Shipment lookup + status for CR-001 (“no tracking numbers”) and FAQ templates. Stream B1 explicitly calls for this inventory. | Prod required; staging optional (can use sandbox). Dev uses stubs. | Secrets Manager: `rp-mw/<env>/shipstation/api_key`, `rp-mw/<env>/shipstation/api_secret`, `rp-mw/<env>/shipstation/api_base`. | Owner: Ops / Logistics. **Blocked:** need confirmation whether ShipStation vs Shopify native is authoritative ([Active workstreams](../REHYDRATION_PACK/03_ACTIVE_WORKSTREAMS.md#stream-b1--sprint-0-preflight-access--secrets-inventory)). |
| Email provider / SMTP-forwarding login | Richpanel needs a connected support inbox, see vendor doc “[Connect your Support Email](../reference/richpanel/Non_Indexed_Library/Connect_your_Support_Email.txt)”. Also required to satisfy Stream B1 (“inventory required accounts/keys — AWS, Richpanel, email provider, shipping platform”). | Prod inbox mandatory; staging optional via forwarding; dev uses mocks. | Store OAuth app password / SMTP credentials in Secrets Manager `rp-mw/<env>/email/<provider>/*`. If AWS SES is used, also store SMTP user + DKIM keys. | Owner: CX / IT. **Pending:** need to confirm provider (Gmail vs O365 vs SES) and supply forwarding credentials. |
| Runtime feature flags (`safe_mode`, `automation_enabled`) | Operator kill switches per [Kill Switch and Safe Mode](../06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md). Flags must be editable without redeploy. | `dev`, `staging`, `prod` | AWS Systems Manager Parameter Store `/rp-mw/<env>/safe_mode` and `/rp-mw/<env>/automation_enabled` (created by CDK with defaults). | Owner: Engineering + Support Ops for toggles. **Pending:** finalize IAM guardrails for who can edit parameters + incident playbook linkage. |

---

## 2) AWS account + role requirements

- **Accounts (created):** per `infra/cdk/lib/environments.ts`:
  - `dev`: `151124909266` (`us-east-2`)
  - `staging`: `260475105304` (`us-east-2`)
  - `prod`: `878145708918` (`us-east-2`)
- **CI/CD (OIDC deploy role exists):**
  - GitHub Actions uses the OIDC provider `token.actions.githubusercontent.com` in each account.
  - Deploy workflows assume: `arn:aws:iam::<account_id>:role/rp-ci-deploy` (see `.github/workflows/deploy-*.yml`).
  - Trust policy allows `sts:AssumeRoleWithWebIdentity` for `repo:KevinSGarrett/RichPanel:*` with audience `sts.amazonaws.com` (see `trust-ci-*.json`).
- **Runtime execution roles:** Lambda execution roles are created by CDK per stack/function (not manually named). Access is constrained via least-privilege policies attached by the stack.
- **Human access:** Prefer IAM Identity Center/SSO with MFA; monthly access reviews must verify who can read prod secrets (see break-glass doc §1–§3).
- **Action items:** ensure CloudTrail + baseline guardrails are enabled in all accounts and keep OIDC trust conditions tight (repo + branch/tag constraints where appropriate).

---

## 3) Richpanel API + webhook credentials

1. **API keys (per env):**
   - Documented in [Secrets and Key Management §1–§4](../06_Security_Privacy_Compliance/Secrets_and_Key_Management.md).
   - Naming convention in Secrets Manager: `rp-mw/<env>/richpanel/api_key`.
   - Non-prod fallback: if only a single Richpanel workspace exists, stage can reuse a limited-scope key but must only act on tagged test tickets (see [Env strategy §Richpanel](../09_Deployment_Operations/Environments.md#richpanel-environment-strategy)).
   - Optional token pool (rate-limit smoothing):
     - Enable with `RICHPANEL_TOKEN_POOL_ENABLED=true`.
     - Provide comma-separated secret IDs via `RICHPANEL_TOKEN_POOL_SECRET_IDS` (each should be a Richpanel API key secret).
2. **Webhook endpoint + token:**
   - Endpoint: `POST /richpanel/inbound` per [Webhooks doc §6.1](../03_Richpanel_Integration/Webhooks_and_Event_Handling.md#6-middleware-ingress-contract).
   - Shared-secret header: `X-Middleware-Token` per §4.1 of the same doc.
   - Secrets Manager path: `rp-mw/<env>/richpanel/webhook_token`.
   - Token must also be copy-pasted into the Richpanel HTTP Target configuration; never exposed in `.env` or logs.
3. **Rotation + audit:**
   - Rotate quarterly or during personnel changes (see [Secrets doc §4](../06_Security_Privacy_Compliance/Secrets_and_Key_Management.md#4-key-rotation-v1)).
   - Track rotations in `Change_Log.md` and ensure CloudTrail alerts on HTTP target updates.

---

## 4) OpenAI access

- Required for routing + FAQ automation per [Environments §OpenAI](../09_Deployment_Operations/Environments.md#openai-environment-strategy).
- Secrets Manager naming: `rp-mw/<env>/openai/api_key`, optional additional metadata (model, org id) stored as non-secret parameters.
- Dev/staging keys should enforce lower spend limits and disable data retention (set `store=false`).
- Prod key should be isolated and accessible only to `rp-mw-worker`/`ci-deploy` roles; humans use eval harness offline.
- Outstanding: request billing ownership + API key issuance from leadership, then capture ARNs in this doc once created.

---

## 5) ShipStation / marketplace credentials

- Stream B1 explicitly lists “shipping platform credentials” as a blocker ([Active workstreams](../REHYDRATION_PACK/03_ACTIVE_WORKSTREAMS.md#stream-b1--sprint-0-preflight-access--secrets-inventory)).
- Required data (regardless of platform):
  1. API key / client id.
  2. API secret / client secret.
  3. Base URL and version (e.g., `https://ssapi.shipstation.com`).
  4. Webhook or event callback URLs (if we subscribe to fulfilment events later).
- Storage plan: Secrets Manager `rp-mw/<env>/shipstation/api_key`, `rp-mw/<env>/shipstation/api_secret`, `rp-mw/<env>/shipstation/api_base`. Non-prod can use sandbox keys or mock services if vendor does not offer test tenants (fallback noted in [Environments §Shopify](../09_Deployment_Operations/Environments.md#shopify-environment-strategy)).
- Outstanding decisions:
  - Confirm whether ShipStation or Shopify is the source of truth for shipment data (ties into CR-001 “no tracking numbers” guardrails).
  - Identify human owner (likely Operations) and ensure they can rotate credentials without involving engineering.

### Shopify Admin API token (if Shopify is used for commerce reads)

- Canonical secret name (Shopify Admin API token): `rp-mw/<env>/shopify/admin_api_token`
- Legacy/fallback secret name (supported by client for compatibility): `rp-mw/<env>/shopify/access_token`
- Notes:
  - Keep scope minimal (read-only where possible).
  - Prefer creating a dedicated non-prod token for `dev`/`staging` if the store supports it.
  - Shopify OAuth client credentials live in Secrets Manager:
    - `rp-mw/<env>/shopify/client_id`
    - `rp-mw/<env>/shopify/client_secret`
  - Expected token secret JSON shape for refreshable tokens:
    - `{"access_token":"...","refresh_token":"...","expires_at":1700000000}`
    - `expires_at` is a Unix epoch timestamp (seconds).

---

## 6) Email provider / inbox credentials

- Richpanel requires a connected support email channel; vendor guidance covers Gmail, M365, WorkMail, and others ([reference doc](../reference/richpanel/Non_Indexed_Library/Connect_your_Support_Email.txt)).
- Minimum assets to inventory:
  - Provider type (Gmail, Microsoft 365, AWS SES, etc.).
  - App password or OAuth client with IMAP/SMTP scopes.
  - DKIM/SPF configuration (if AWS SES is the outbound relay, confirm SPF entries per vendor note “Preventing Email Delivery Issues by Adding AWS SES to SPF Records”).
- Storage plan: Secrets Manager `rp-mw/<env>/email/{provider}/smtp_username`, `smtp_password`, `imap_token`, etc. Only automation bridges should read these (if we automate fallback replies); otherwise keep them with CX but ensure retrieval path is documented.
- Outstanding: CX/IT must confirm which mailbox (support@, orders@) is authoritative and provide either forwarding credentials or SES SMTP credentials for prod. Without this, we cannot validate outbound reply paths.

---

## 7) Secrets handling + variable mapping

- All secrets live in AWS Secrets Manager (never in `.env`), per [Secrets and Key Management](../06_Security_Privacy_Compliance/Secrets_and_Key_Management.md#2-storage-location-required).
- Non-secret environment variables (see `config/.env.example`) define *names* or safe defaults only:
  - `RICH_PANEL_ENV`, `AWS_REGION`, webhook path, API base URLs, provider identifiers.
  - Secret-bearing keys remain as **blank placeholders** so developers know they must source from Secrets Manager.
- Runtime feature flags now live in AWS Systems Manager Parameter Store (per CDK stack outputs):
  - `/rp-mw/<env>/safe_mode` (default `false`)
  - `/rp-mw/<env>/automation_enabled` (default `true`)
  - Update flags via console/CLI per kill-switch runbook; do not add them to `.env`.
- Deployment workflow: CI/CD injects secret values at deploy time by resolving Secrets Manager ARNs and setting Lambda environment variables or SSM parameters. Developers copy `.env.example` → `.env` locally and fill values from their personal AWS account (dev only).

---

## 8) Open issues & next steps

1. **Provision AWS org + accounts** — Owner: Engineering. Needed for Sprint 1 IaC to run `cdk bootstrap`.
2. **Request Richpanel keys + webhook token** — Owner: CX Ops. Need workspace admin to mint keys, then record ARN references here.
3. **Decide shipping data source (ShipStation vs Shopify)** — Owner: Ops/Logistics. Blocks creation of Secrets Manager namespace for commerce integrations.
4. **Confirm email provider + forwarding plan** — Owner: CX/IT. Need at least prod credentials plus DKIM/SPF updates before enabling outbound automation.
5. **Populate Secrets Manager namespaces** — Owner: Engineering once credentials exist. Ensure naming matches the patterns documented above and enforce rotation alarms.

Once each blocker is cleared, update the relevant row in §1 and reference the secret ARN/owner for traceability.

