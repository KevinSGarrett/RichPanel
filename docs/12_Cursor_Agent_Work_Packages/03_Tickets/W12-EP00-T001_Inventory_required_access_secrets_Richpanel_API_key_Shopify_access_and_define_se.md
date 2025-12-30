# W12-EP00-T001 — Inventory required access + secrets (Richpanel API key, Shopify access) and define secret storage plan

Last updated: 2025-12-23

## Owner / Agent (suggested)
Ops/Infra

## Objective
Establish which credentials are required for dev/staging/prod and where they will live (Secrets Manager / SSM), without storing secrets in repo.

## Context / References
- `docs/02_System_Architecture/AWS_Organizations_Setup_Plan_No_Control_Tower.md`
- `docs/06_Security_Privacy_Compliance/Secrets_and_Key_Management.md`
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`
- `docs/05_FAQ_Automation/Order_Status_Automation.md`

## Dependencies
- (none)

## Implementation steps
1. Create a credential inventory table: service → credential → environment(s) → owner → rotation cadence.
1. Confirm Richpanel API key exists and is scoped appropriately for ticket/tag/order operations.
1. Confirm whether Shopify Admin API credentials exist; if unknown, document as pending but define the expected scopes for later.
1. Create AWS Secrets Manager naming conventions and SSM Parameter namespaces (dev/staging/prod).
1. Document operational procedure for updating secrets and verifying the middleware reads the new values.

## Acceptance criteria
- [ ] Credential inventory table exists and is stored in docs (no secrets).
- [ ] Secrets naming convention and environment separation documented.
- [ ] Rotation cadence documented for each credential type.

## Test plan
- Manual: demonstrate that dev environment can read a placeholder secret from Secrets Manager using least-privilege role.
- Manual: confirm no secrets committed to repository.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- No secrets in git; use Secrets Manager / SSM only.
- Enable rotation plan where supported.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
