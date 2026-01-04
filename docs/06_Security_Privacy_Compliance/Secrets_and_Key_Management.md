# Secrets and Key Management (OpenAI, Richpanel, Shopify)

Last updated: 2025-12-22

This document defines how we manage credentials safely across dev/staging/prod.

Related:
- Webhook rotation: `Webhook_Secret_Rotation_Runbook.md`
- Kill switch / safe mode: `Kill_Switch_and_Safe_Mode.md`
- Incident response: `Incident_Response_Security_Runbooks.md`


---

## 1) Secrets in scope
- Richpanel API key (`x-richpanel-key`)
- OpenAI API key
- Shopify Admin API access token (if used)
- Webhook auth secret (HMAC or shared token)
- Internal signing keys (if any)

---

## 2) Storage location (required)
- **AWS Secrets Manager** is the default store.
- No secrets in:
  - repos
  - CI logs
  - Lambda environment variables (unless injected at deploy time from Secrets Manager)
  - Richpanel macros
  - Slack messages

**Pattern:**
- Lambda reads secret values at startup (cached) or via AWS Parameter Store with secure string.

**OpenAI key loading**
- Stored at `rp-mw/<env>/openai/api_key` in Secrets Manager (env resolved via `RICHPANEL_ENV` → `RICH_PANEL_ENV` → `MW_ENV` → `ENVIRONMENT` → `local`, then lowercased).
- Runtime loads from Secrets Manager first; `OPENAI_API_KEY` stays as an optional override for local/offline runs (network stays disabled by default).

---

## 3) Environment separation (required)
We use separate AWS accounts for dev/staging/prod.
Each environment has:
- unique OpenAI key(s)
- unique Richpanel key(s) (if possible)
- unique webhook tokens

Never reuse prod keys in non-prod.

---

## 4) Key rotation (v1)
### 4.1 Rotation schedule
- Webhook token/HMAC secret: rotate quarterly (or immediately after any suspected exposure)
- OpenAI API key: rotate quarterly
- Richpanel key: rotate quarterly (or per staff changes if keys are user-bound)
- Shopify token: rotate per Shopify governance

### 4.2 Rotation runbook (minimum steps)
1) Create new secret version in Secrets Manager
2) Deploy middleware (dev → staging → prod) reading new secret version
3) Update Richpanel HTTP Target headers/token
4) Verify inbound webhook succeeds
5) Deactivate old key

---

## 5) OpenAI-specific key safety (required)
- Keys must never be in client-side code (browser/mobile).
- Use separate keys per environment.
- Use usage monitoring and budgets to detect abuse quickly.

(Reference: OpenAI “Best Practices for API Key Safety”.)

---

## 6) Access control
- Only a small set of admins may read prod secrets.
- Developers use non-prod secrets.
- Use break-glass procedure for emergency access (documented in incident runbooks).

---

## 7) Logging policy for secrets
- Never log headers or full request bodies that might contain tokens.
- If token is in URL (fallback option), ensure logs do not include full URL query/path in plaintext.