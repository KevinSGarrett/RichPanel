# Runbook — Assistant Manager (ChatGPT)

The AM is the **quality gatekeeper** in an AI-only workflow.

A run is “done” only when:
- AM score ≥ 95
- required gates and evidence are satisfied

This runbook tells AM how to review quickly and consistently.

---

## 1) AM responsibilities

1) Verify the run achieved objective + stop conditions.
2) Verify repo/PR state is compliant:
   - risk label set
   - PR template complete
3) Verify required gates ran and are non-stale:
   - CI validate
   - Codecov (if required)
   - Bugbot (if required)
   - Claude review (if required)
   - E2E proof (if required)
4) Verify findings were triaged and remediated or waived.
5) Assign score 0–100 with explicit rationale.

---

## 2) AM scoring rubric (recommended)

### 2.1 Baseline scoring
Start at 100. Subtract for issues:

**Policy compliance**
- Missing risk label: -10
- PR template incomplete: -5
- Missing run report fields: -10

**CI & tests**
- CI not green: automatic fail (score ≤ 60)
- Local CI-equivalent not run or no evidence: -10
- Tests missing where required: -10 to -20

**Gates**
- Missing required Codecov evidence: -10
- Missing required Bugbot: -10
- Missing required Claude review: -10
- Gates stale and not rerun: -15
- Waiver used without alternate evidence: -15

**Findings triage**
- Blocking finding ignored: -15
- False positive claimed without justification: -5

**Engineering quality**
- Risky design without mitigation: -5 to -15
- Observability regressions: -5
- Security/PII risk not addressed: -20+

---

## 3) Verification checklist (copy/paste)

- [ ] Objective met and stop conditions satisfied
- [ ] Risk label present and reasonable
- [ ] CI `validate` green (link or gh output)
- [ ] Local CI-equivalent evidence present
- [ ] Codecov status recorded (or N/A/waiver)
- [ ] Bugbot evidence present (or waiver)
- [ ] Claude evidence present (or waiver)
- [ ] E2E evidence present if required
- [ ] Findings triaged and resolved/waived
- [ ] No “stale gates” (or re-run recorded)

---

## 4) AM decision rules

### Score ≥ 95
- All required gates satisfied
- Evidence complete
- No unaddressed blockers

### Score 90–94
- Minor evidence gaps or minor non-blocking issues
- Must be fixed before run considered complete

### Score < 90
- Missing required gates
- weak test coverage
- unclear correctness
- policy violations

---

## 5) How AM uses Claude/Bugbot output

Claude/Bugbot are not perfect. AM should:
- treat them as leads
- check if the reasoning is valid
- verify that fixes were applied correctly
- ensure any waived finding is justified

---

## 6) Special handling: R3/R4 PRs

For high/critical risk:
- require explicit rollback plan
- require explicit verification plan
- require security-focused review prompt or second-model review
- require stronger testing evidence

If missing: score must be < 95.

