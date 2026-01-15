# Label taxonomy

Labels are how we make the workflow **machine-enforceable**.

This taxonomy is designed for:
- risk-based gate selection
- cost controls (avoid heavy gates on tiny PRs)
- staleness detection (“reviewed then changed”)

---

## 1) Risk labels (exactly one required)

- `risk:R0-docs`
- `risk:R1-low`
- `risk:R2-medium`
- `risk:R3-high`
- `risk:R4-critical`

---

## 2) Gate lifecycle labels (optional but recommended)

### Gate state
- `gates:ready`  
  PR is stable and ready to run Bugbot/Claude/coverage gates.

- `gates:running`  
  Gate workflows are in-flight.

- `gates:passed`  
  Required gates complete for the current PR state.

- `gates:stale`  
  New commits landed after gates. Must re-run.

### Gate forcing / rerun
- `gates:rerun`  
  Force rerun even if policy would normally skip.

---

## 3) Waiver label

- `waiver:active`  
  A waiver exists and must be documented in PR description + run report.

---

## 4) Domain labels (optional but helpful)

- `domain:backend`
- `domain:infra`
- `domain:frontend`
- `domain:security`
- `domain:observability`
- `domain:automation`

---

## 5) Automation labels (optional)

- `automation:bugbot`
- `automation:claude`
- `automation:codecov`

These can be used if you want to trigger specific workflows.

---

## 6) How labels are applied

### By PM (preferred)
- PM chooses risk label based on classification algorithm.

### By Cursor agents
- Agents may apply labels using GitHub CLI:
  - `gh pr edit <PR#> --add-label "risk:R2-medium"`
  - `gh pr edit <PR#> --add-label "gates:ready"`

### By automation
- On new commits, a workflow can apply `gates:stale` and remove `gates:passed`.

