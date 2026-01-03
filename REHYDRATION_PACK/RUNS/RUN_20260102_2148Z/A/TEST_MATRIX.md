# Test Matrix

**Run ID:** `RUN_20260102_2148Z`  
**Agent:** A  
**Date:** 2026-01-02

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Deploy Dev Stack (dev) | `gh workflow run deploy-dev.yml --ref fix/align-cdk-account-ids` | pass | [Actions run #20670472539](https://github.com/KevinSGarrett/RichPanel/actions/runs/20670472539) |
| Deploy Dev Stack (main) | `gh workflow run deploy-dev.yml --ref main` | pass | [Actions run #20671373249](https://github.com/KevinSGarrett/RichPanel/actions/runs/20671373249) |
| CI checks | `python scripts/run_ci_checks.py` | pass | local log |
| Deploy Staging Stack (main) | `gh workflow run deploy-staging.yml --ref main` | pass | [Actions run #20673604749](https://github.com/KevinSGarrett/RichPanel/actions/runs/20673604749) |
| Staging E2E Smoke (main) | `gh workflow run staging-e2e-smoke.yml --ref main -f event-id=evt:20260103003757` | pass | [Actions run #20673641283](https://github.com/KevinSGarrett/RichPanel/actions/runs/20673641283) |
| Deploy Prod Stack (main) | `gh workflow list --limit 200` (confirm `Deploy Prod Stack` exists) | not run (prod deploy on-demand) | `.github/workflows/deploy-prod.yml` added; release will trigger `workflow_dispatch` on main |

## Notes
- First deploy attempt on `main` failed while still using placeholder bootstrap account (run `20670461957`); reran on feature branch after updating IDs to prove fix.  
- Deploy run succeeded once the branch with corrected accounts was used (see link above).
- Staging E2E smoke initially failed (run `20673607764`) due to timing - test ran before deploy completed. Reran after deploy finished (run `20673641283`) and passed successfully.
