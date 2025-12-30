# Wave 09 — Testing strategy, QA plan, and release readiness

Last updated: 2025-12-22  
Status: **Complete ✅** (Update 2 closeout)

This wave translates the design work from Waves 01–08 into a **testable, releasable plan**.

---

## Wave goal
Create a production-grade testing and release plan that ensures:
- safety (no automation loops, no data disclosure, Tier 0 never automated)
- reliability (ACK fast, duplicates handled, rate-limit resilience)
- quality (routing + automation performs acceptably and regressions are gated)
- operability (kill switch + rollback + monitoring)

---

## Deliverables (definition of done)
### Testing
- [x] Test strategy + matrix (unit → e2e → load)
- [x] Integration test plan (stubs + optional staging smoke)
- [x] Contract test plan (schemas + fixtures)
- [x] Manual QA checklists (pre-prod)
- [x] Load/soak test plan tied to heatmap and rate-limit scenarios
- [x] Test data and fixtures strategy (PII-safe)
- [x] Smoke test pack mapping directly to Wave 05 templates/playbooks + Tier policies

### Release readiness
- [x] CI/CD plan (gates + prompt/template promotion)
- [x] Environments plan (dev/staging/prod safety defaults)
- [x] Release and rollback plan (progressive enablement)
- [x] Go/No-Go checklist
- [x] First production deploy runbook (step-by-step + rollback levers)

---

## Progress summary

### Update 1 (delivered)
- Expanded:
  - `docs/08_Testing_Quality/Test_Strategy_and_Matrix.md`
  - `docs/08_Testing_Quality/Load_and_Soak_Testing.md`
- Added:
  - `docs/08_Testing_Quality/Integration_Test_Plan.md`
  - `docs/08_Testing_Quality/Contract_Tests_and_Schema_Validation.md`
  - `docs/08_Testing_Quality/Manual_QA_Checklists.md`
  - `docs/08_Testing_Quality/Test_Data_and_Fixtures.md`
- Expanded deployment/release docs:
  - `docs/09_Deployment_Operations/CICD_Plan.md`
  - `docs/09_Deployment_Operations/Environments.md`
  - `docs/09_Deployment_Operations/Release_and_Rollback.md`
  - Added `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`

### Update 2 (closeout)
- Added smoke test pack:
  - `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
  - `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`
- Added first production deploy runbook:
  - `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`
- Tightened Go/No-Go checklist and linked smoke pack + runbook
- Updated trackers and marked Wave 09 complete

---

## Risks / concerns to watch (still relevant in build phase)
- Staging may not have a separate Richpanel workspace; mitigate with stubs and safe_mode defaults.
- Load tests must simulate vendor rate limits; otherwise we get false confidence.
- Always verify kill switch works before enabling automation.

---

## Deferred items (not blocking Wave 09 completion)
Richpanel tenant capability verification remains deferred and tracked in `docs/00_Project_Admin/Open_Questions.md`.
