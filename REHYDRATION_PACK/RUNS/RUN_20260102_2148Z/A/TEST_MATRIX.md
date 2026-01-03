# Test Matrix

**Run ID:** `RUN_20260102_2148Z`  
**Agent:** A  
**Date:** 2026-01-02

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Deploy Dev Stack (dev) | `gh workflow run deploy-dev.yml --ref fix/align-cdk-account-ids` | pass | [Actions run #20670472539](https://github.com/KevinSGarrett/RichPanel/actions/runs/20670472539) |
| CI checks | `python scripts/run_ci_checks.py` | pass | local log |

## Notes
- First deploy attempt on `main` failed while still using placeholder bootstrap account (run `20670461957`); reran on feature branch after updating IDs to prove fix.  
- Deploy run succeeded once the branch with corrected accounts was used (see link above).
