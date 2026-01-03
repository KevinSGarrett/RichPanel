# Test Matrix

**Run ID:** `RUN_20260102_2148Z`  
**Agent:** C  
**Date:** 2026-01-02

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Repo CI contract | `python scripts/run_ci_checks.py --ci` | fail (repo already had regenerated docs + trust artifacts modified outside this change-set, so script aborts) | Local terminal log 2026-01-02 22:xxZ (see run transcript) |
| Dev E2E smoke workflow (dispatch readiness) | `gh workflow run dev-e2e-smoke.yml --ref <branch> -f event-id=<VALUE>` | blocked (requires GitHub token + AWS creds not available in this workspace) | https://github.com/KevinSGarrett/RichPanel/actions/workflows/dev-e2e-smoke.yml — trigger in GitHub UI/CLI to capture run URL + job summary evidence |

## Notes
- Local CI command now fails because upstream dev already regenerated docs/trust artifacts; once that noise is committed, rerun `python scripts/run_ci_checks.py --ci` to confirm green.
- The new workflow writes AWS evidence links to the job summary automatically; record that URL in this table after the first dispatch under the PM’s credentials.
