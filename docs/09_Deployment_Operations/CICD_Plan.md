# CI/CD Plan

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

This document defines how code, configuration, and prompt/template changes move safely from dev → staging → prod.

---

## Goals
- Every production change is **traceable**, **tested**, and **reversible**.
- Prompt/template changes follow **the same rigor** as code changes.
- CI gates enforce safety and quality invariants.

---

## Artifacts we deploy
1) **Application code**
- Lambda handlers (ingress + worker)
- shared libraries (policy engine, schema validation, template rendering)

2) **Infrastructure as Code (IaC)**
- API Gateway
- SQS + DLQ
- DynamoDB
- IAM roles/policies
- log retention + alarms

3) **Configuration**
- parameter defaults (Wave 07)
- security settings and secrets references (Wave 06)
- feature flags (safe_mode, automation_enabled)

4) **LLM artifacts**
- prompts (Wave 04)
- schemas (Wave 04)
- model config (Wave 04)
- template_id catalog + templates (Wave 05)

---

## Branching and promotion (recommended)
- `main` = production-ready
- feature branches → PR → merge to main
- deployments:
  - merge to main → deploy to **dev**
  - tagged release (or manual promote) → deploy to **staging**
  - manual approval → deploy to **prod**

---

## Required CI jobs (merge gates)
These run on every PR:

1) **Lint + format + static checks**
2) **Unit tests**
   - policy engine
   - templates
   - redaction
3) **Component tests**
   - ingress + worker with mocks
4) **Contract tests**
   - schema validation
   - fixture parsing tests

5) **Security checks**
   - secret scanning
   - dependency vulnerability scan (baseline)
   - IaC policy lint (if used)

---

## Conditional CI jobs (required for certain changes)
### Prompt/template changes
If PR modifies:
- prompts (`docs/04_LLM_Design_Evaluation/prompts/`)
- schemas (`docs/04_LLM_Design_Evaluation/schemas/`)
- templates (`docs/05_FAQ_Automation/templates/`)
then CI must additionally run:

- **LLM eval regression gates**
  - golden set eval
  - Tier 0 FN gate
  - Tier 2 violation gate
  - schema validity gate

See:
- `docs/08_Testing_Quality/LLM_Evals_in_CI.md`
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

---

## Deployment pipeline (recommended stages)

### Stage 1 — Deploy to dev
- run smoke tests
- safe_mode can be on/off (dev)

### Stage 2 — Deploy to staging
- safe_mode defaults ON
- automation_enabled defaults OFF
- run:
  - integration tests (with stubs)
  - manual QA checklist subset (Wave 09)

### Stage 3 — Promote to prod
- requires go/no-go approval
- deploy with safe_mode ON and automation_enabled OFF for initial release (routing only)
- gradual enablement follows `Release_and_Rollback.md`

---

## Change management (required)
Every production release should produce:
- release note entry in `Change_Log.md`
- updated `Decision_Log.md` if behavior changes
- link to CI run artifact (tests + eval)

---

## Rollback principle
Rollback must be possible in **two ways**:
1) **Configuration rollback** (fast)
   - disable automation or safe_mode on (Wave 06 kill switch)
2) **Code rollback** (slower)
   - deploy previous version

See:
- `docs/09_Deployment_Operations/Release_and_Rollback.md`
