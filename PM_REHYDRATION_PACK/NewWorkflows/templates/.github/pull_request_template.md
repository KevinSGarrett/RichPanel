<!--
RichPanel PR Template (AI-only workflow)

Rules:
- Exactly ONE risk checkbox must be selected AND the corresponding risk label must be applied.
- For R2+ PRs, do not claim "done" until gates are completed and evidence links are present.
-->

# Summary

## Run metadata (required)
- RUN_ID:
- Agent: A / B / C
- PM objective:
- Stop conditions met: yes/no

## What changed
- (bullets)

## Why
- (bullets)

---

# Risk classification (required)

Select ONE:

- [ ] R0 Docs-only  (`risk:R0-docs`)
- [ ] R1 Low        (`risk:R1-low`)
- [ ] R2 Medium     (`risk:R2-medium`)
- [ ] R3 High       (`risk:R3-high`)
- [ ] R4 Critical   (`risk:R4-critical`)

**Risk rationale (required):**
- Impact:
- Blast radius:
- Reversibility:
- Observability:
- Security/PII:

---

# Gate plan (required)

Fill based on `policies/02_GATE_MATRIX.md`.

- CI validate required: yes/no
- Codecov required: N/A / advisory / required
- Bugbot required: N/A / optional / required
- Claude review required: N/A / optional / required
- E2E required: N/A / conditional / required

---

# Evidence (required for merge)

## CI
- GitHub Actions run link:
- Local CI-equivalent run:
  - command: `python scripts/run_ci_checks.py --ci`
  - result: PASS/FAIL
  - snippet/log link:

## Codecov
- Patch status: PASS/FAIL/N/A
- Project status: PASS/FAIL/N/A
- Notes / remediation:

## Bugbot
- Triggered: yes/no/N/A
- Bugbot comment permalink:
- Findings summary + actions:

## Claude review
- Triggered: yes/no/N/A
- Output link (comment or check):
- Verdict: PASS/CONCERNS/FAIL
- Actions:

## E2E proof (if required)
- Evidence folder/link:
- Scenario(s):
- Outcome:

---

# Waivers (if any)

If any gate is waived, paste the waiver template here and add label `waiver:active`.

---

# Rollback / verification plan (required for R3/R4)

- Rollback plan:
- Post-merge verification steps:
- Monitoring signals to watch:

---

# Checklist (author)

- [ ] Risk label applied (`risk:*`)
- [ ] PR is focused and minimal diff
- [ ] Local CI-equivalent PASS
- [ ] CI `validate` green
- [ ] Required gates executed (or waived with alternate evidence)
- [ ] Findings triaged and resolved/waived
- [ ] Gates not stale (no new commits since last review gates)
- [ ] AM score ≥ 95 references evidence

