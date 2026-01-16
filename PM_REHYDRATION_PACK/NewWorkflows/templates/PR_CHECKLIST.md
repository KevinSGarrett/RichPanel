# PR checklist (author)

This checklist is meant to be copied into PR description **or** verified by the agent run report.

---

## Scope & hygiene
- [ ] PR contains a single coherent objective (no scope creep)
- [ ] Diff is minimized (no accidental formatting churn)
- [ ] No secrets/PII in diff, comments, or logs

## Risk & labels
- [ ] Exactly one risk label applied (`risk:R0-docs` / `risk:R1-low` / `risk:R2-medium` / `risk:R3-high` / `risk:R4-critical`)
- [ ] Risk rationale written in PR description
- [ ] `gates:ready` applied only when PR is stable

## Local checks
- [ ] Ran: `python scripts/run_ci_checks.py --ci`
- [ ] Result: PASS
- [ ] Output snippet recorded in run report

## CI checks
- [ ] GitHub required check `validate` is green
- [ ] No failing optional checks relevant to this change

## Codecov (when required)
- [ ] `codecov/patch` PASS (or waiver)
- [ ] `codecov/project` PASS when required (or waiver)
- [ ] Any coverage drops explained and remediated

## Bugbot (when required)
- [ ] Bugbot triggered on stable diff
- [ ] Findings triaged (fixed/false positive/waived)
- [ ] Bugbot comment permalink recorded

## Claude review (when required)
- [ ] Claude semantic review run on stable diff
- [ ] Verdict PASS or concerns remediated/waived
- [ ] Output link recorded

## E2E (when required)
- [ ] E2E scenario executed
- [ ] Evidence saved under `qa/test_evidence/<RUN_ID>/`
- [ ] Evidence link recorded

## Waivers (if any)
- [ ] Waiver template filled
- [ ] Alternate evidence provided
- [ ] `waiver:active` label applied

