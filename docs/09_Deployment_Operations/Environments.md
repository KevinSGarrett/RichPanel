# Environments (Dev/Staging/Prod)

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

This document defines how environments are separated so tests don’t harm customers, leak data, or create confusion.

---

## Recommended environment model (v1)
We use **separate AWS accounts** for:
- dev
- staging
- prod

(Organizations is recommended; Control Tower is optional and deferred for v1.)

---

## Multi-account preflight (required)
Before any secrets-backed run, verify the AWS account/region and required secrets
match the intended environment. This prevents accidentally drifting into the wrong
AWS account (dev vs prod) or region.

Run locally (PII-safe):
```bash
python scripts/aws_account_preflight.py --env dev --region us-east-2
python scripts/secrets_preflight.py --env dev --region us-east-2 --out artifacts/preflight_dev.json
```

Expected behavior:
- Fails fast if the AWS account id does not match the environment.
- Fails fast if required secrets or SSM kill-switch parameters are missing or unreadable.

---

## Environment purposes

### Dev
- Fast iteration
- Uses stubs/mocks for vendors by default
- No customer data required
- Can run synthetic webhook payloads

### Staging
- Production-like configuration
- Safe-mode defaults:
  - `safe_mode=true`
  - `automation_enabled=false`
- Uses:
  - vendor stubs by default
  - optional sandbox/test vendor accounts if available

### Prod
- Real traffic
- Release uses progressive enablement:
  - routing only first (safe_mode ON)
  - then limited automation (template whitelist) once validated

---

## Richpanel environment strategy (important)
We do **not** assume you have a staging Richpanel workspace.

We support 3 options (best → fallback):

1) **Separate Richpanel workspace for staging** (best)
- separate API key
- safe test tickets
- no risk of affecting production

2) **Same workspace, but “test-only” tickets** (acceptable)
- only interact with tickets created in a test channel / tagged `mw-test`
- middleware must ignore all other tickets in staging mode

3) **No Richpanel at all in staging** (fallback)
- use stubs for all Richpanel calls
- validate integration via contract + integration tests

---

## Shopify environment strategy
- There is **no Shopify sandbox/dev store**; all environments read from the **live store** only.
- Use stubs in dev/staging when Shopify reads are not required.
- In prod, only disclose tracking/status when deterministic match exists (Tier 2).

---

## OpenAI environment strategy
- Dev/staging: use `store=false` and keep prompts/templates stable.
- CI: use offline eval harness to avoid calling vendors.
- Prod: use the configured production key; never log raw prompts/responses.

---

## Environment configuration rules (non-negotiable)
- Separate secrets per environment (Secrets Manager).
- Feature flags must exist in every env:
  - `safe_mode`
  - `automation_enabled`
  - per-template enablement (optional)
- Logs must be redacted in every env.

---

## Naming and tagging conventions
All resources should be tagged with:
- `env` (dev/staging/prod)
- `service` (richpanel-middleware)
- `owner`
- `cost-center` (optional)

---

## Exit criteria (Wave 09)
Wave 09 considers environments “defined” when:
- the safety defaults are explicit
- staging can run tests without contacting real customers
- promotion path is defined (CI/CD plan)
