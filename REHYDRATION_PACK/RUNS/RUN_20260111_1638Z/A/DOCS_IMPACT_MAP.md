# Docs Impact Map

**Run ID:** `RUN_20260111_1638Z`  
**Agent:** A  
**Date:** 2026-01-11

## Documentation changes

### New documents
- **docs/08_Engineering/E2E_Test_Runbook.md**
  - Type: Canonical runbook
  - Purpose: Comprehensive E2E testing procedures for dev/staging/prod
  - Audience: Cursor agents, PM, reviewers
  - Cross-refs:
    - Referenced from docs/08_Engineering/CI_and_Actions_Runbook.md (section 10)
    - References .github/workflows/dev-e2e-smoke.yml
    - References .github/workflows/staging-e2e-smoke.yml
    - References .github/workflows/prod-e2e-smoke.yml
    - References scripts/dev_e2e_smoke.py

- **REHYDRATION_PACK/09_NEXT_10_SUGGESTED_ITEMS.md**
  - Type: Living document
  - Purpose: Track emerging priorities and follow-up work
  - Audience: Agents, PM
  - Cross-refs:
    - Referenced from REHYDRATION_PACK/05_TASK_BOARD.md

### Updated documents
- **REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md**
  - Section added: PR Health Check (after pre-commit checklist)
  - Impact: All future agent runs will follow PR health check procedures
  - Cross-refs:
    - References docs/08_Engineering/CI_and_Actions_Runbook.md
    - References docs/08_Engineering/E2E_Test_Runbook.md

- **REHYDRATION_PACK/TEMPLATES/Agent_Run_Report_TEMPLATE.md**
  - Section added: PR Health Check (after CI validation evidence)
  - Impact: All future run reports will capture PR health check evidence
  - Fields added: CI status, Codecov status, Bugbot review, E2E testing

- **docs/08_Engineering/CI_and_Actions_Runbook.md**
  - Section added: 10. PR Health Check (required before every merge)
  - Section renumbered: 11. Seed Secrets Manager (was 10)
  - Section renumbered: 12. If you cannot fix quickly (was 11)
  - Impact: PR health check is now formally documented in CI runbook
  - Cross-refs:
    - References docs/08_Engineering/E2E_Test_Runbook.md
    - References codecov.yml
    - References .github/workflows/bugbot-review.yml

- **REHYDRATION_PACK/05_TASK_BOARD.md**
  - Date updated: 2026-01-11
  - Link added: 09_NEXT_10_SUGGESTED_ITEMS.md
  - Impact: NEXT_10 list now visible from task board

## Registry updates required
- docs/08_Engineering/E2E_Test_Runbook.md needs to be added to doc registry
- Will be picked up by next `python scripts/regen_doc_registry.py` run

## Related documentation
- docs/08_Engineering/CI_and_Actions_Runbook.md (primary runbook for CI + PR health checks)
- docs/08_Engineering/E2E_Test_Runbook.md (new, E2E testing procedures)
- docs/08_Engineering/Developer_Guide.md (may reference PR health check in future)
- REHYDRATION_PACK/05_TASK_BOARD.md (links to NEXT_10 list)
- REHYDRATION_PACK/09_NEXT_10_SUGGESTED_ITEMS.md (new, emerging priorities)

## Documentation style notes
- E2E_Test_Runbook.md follows canonical runbook format (numbered sections, PowerShell-safe examples)
- NEXT_10_SUGGESTED_ITEMS.md uses N10-### ID format for tracking
- PR Health Check sections use consistent structure across templates and runbooks
