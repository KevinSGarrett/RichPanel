# Codecov policy (coverage reporting and gating)

Codecov is a *signal* gate:
- It detects coverage regression and untested new code.
- It is not the same thing as “tests passed”.

In an AI-only workflow, Codecov is valuable because:
- models can accidentally remove tests or reduce coverage
- models may ship “looks correct” logic that lacks regression tests

---

## 1) Terms

### 1.1 Coverage upload
The CI job generates coverage data (e.g., `coverage.xml`) and uploads it to Codecov.

### 1.2 Patch coverage
Coverage on *only the changed lines* in a PR.

### 1.3 Project coverage
Overall repository coverage.

---

## 2) RichPanel current state (from repo)

Your `ci.yml` currently:
- runs unit tests (Python `unittest discover` in `scripts/`)
- produces `coverage.xml`
- uploads coverage via `codecov/codecov-action@v4`

This is a good baseline, but it currently runs anytime CI runs.

---

## 3) Policy: when Codecov is required

### R0 docs-only
- Codecov not required
- “N/A” is acceptable in run report

### R1 low
- Codecov is advisory by default
- If the change adds/changes code paths, patch coverage should be reviewed
- If patch coverage drops significantly, treat it as a concern

### R2+
- Codecov patch coverage is required unless waived
- For R3/R4, project coverage thresholds should also be enforced (recommended)

---

## 4) Policy: what is “passing”

### Patch coverage
- Should not regress beyond allowed threshold.
- Prefer: **patch target = auto**, threshold small (e.g., 1–2%).
- For new files: require non-trivial test coverage, or explicitly justify why not testable.

### Project coverage
- For R3/R4:
  - avoid meaningful project coverage drops
  - if drops, require remediation or waiver + alternate testing

---

## 5) Cost control strategy (avoid running Codecov on tiny pushes)

Codecov’s upload step is tied to CI runs. To reduce waste:

### Strategy A (process-level): batch pushes
- Cursor agents should commit locally as much as needed.
- Only push when:
  - local CI-equivalent is green
  - diff is coherent
This alone reduces Codecov runs dramatically.

### Strategy B (workflow-level): split “fast CI” vs “coverage gate”
- Fast CI runs on every push.
- Coverage + Codecov upload runs only when:
  - label `gates:ready` is set, OR
  - risk is R2+, OR
  - manual workflow_dispatch is triggered.

### Strategy C: skip upload on docs-only
Use `paths-ignore` or an `if:` guard so coverage isn’t computed/uploaded for R0.

---

## 6) Recommended Codecov configuration (codecov.yml)

To make Codecov signals consistent, add a `codecov.yml` at repo root (example):

```yaml
coverage:
  status:
    project:
      default:
        target: auto
        threshold: 1%
    patch:
      default:
        target: auto
        threshold: 1%
comment:
  layout: "reach,diff,flags,files"
  behavior: default
```

Tune targets over time.

---

## 7) Required reporting (run report)

Every PR run report must include:

- Codecov patch status: PASS/FAIL/N/A
- Codecov project status: PASS/FAIL/N/A
- If FAIL:
  - what changed
  - remediation (added tests) or waiver justification

---

## 8) Failure modes and fallback

### Codecov outage / upload error
Allowed waiver reason if alternate evidence exists:
- CI still ran tests successfully
- Coverage file is stored as artifact and summarized
- Additional targeted tests executed (if risk R3+)

Note: avoid using “fail CI if Codecov upload fails” for high-availability gating unless you accept external outages blocking merges.

---

## 9) AM scoring rule

If Codecov is required (R2+):
- missing Codecov evidence or missing remediation/waiver → AM score < 95

