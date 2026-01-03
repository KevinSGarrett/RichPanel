# Test Matrix

**Run ID:** `RUN_20260102_2148Z`  
**Agent:** C  
**Date:** 2026-01-02

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Repo CI contract | `python scripts/run_ci_checks.py --ci` | **pass** (latest run 2026-01-03 02:22Z after staging smoke fixes) | Local terminal log 2026-01-03 02:22Z |
| Deploy Dev Stack | `gh workflow run deploy-dev.yml --ref main` | **pass** | https://github.com/KevinSGarrett/RichPanel/actions/runs/20670764107 |
| Dev E2E smoke (GitHub Actions) | `gh workflow run dev-e2e-smoke.yml --ref main -f event-id=evt:20260103-0230Z` | **fail** — stack `RichpanelMiddleware-dev` only exposes metadata outputs; no ingress HTTP API exists yet so the script cannot derive `IngressEndpointUrl`. | https://github.com/KevinSGarrett/RichPanel/actions/runs/20670901020 (see warnings in job log) |

## Notes
- Repo CI tooling now runs clean locally; see timestamps above.
- Dev stack deploys successfully via OIDC, but the application stack on `main` is still the scaffold (only `CDKMetadata` + naming outputs). Until the event pipeline resources are merged/deployed, the Dev E2E smoke test will continue to fail at the ingress discovery phase. The job summary linked above includes the raw CloudFormation resource inventory for debugging.
- Once the stack exposes the HTTP API/SQS/Dynamo resources, rerun `gh workflow run dev-e2e-smoke.yml ...` and update this table with the success evidence.
