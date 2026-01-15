# Review checklist (PM/AM)

Use this checklist to verify a PR is merge-ready.

---

## Policy compliance
- [ ] Risk label present and matches PR content
- [ ] PR template complete (no placeholders)
- [ ] Evidence links are present and valid
- [ ] Gates are not stale (or re-run recorded)

## CI
- [ ] `validate` green
- [ ] Local CI-equivalent evidence present

## Gates (per risk)
- [ ] Codecov satisfied (or waiver)
- [ ] Bugbot satisfied (or waiver)
- [ ] Claude satisfied (or waiver)
- [ ] E2E satisfied (if required)

## Findings triage
- [ ] No unaddressed blocking findings
- [ ] False positives are justified
- [ ] Waivers are complete and include alternate evidence

## High risk extras (R3/R4)
- [ ] Rollback plan present
- [ ] Verification/monitoring plan present
- [ ] Security/PII concerns explicitly addressed

## AM score
- [ ] AM score ≥ 95 and references evidence

