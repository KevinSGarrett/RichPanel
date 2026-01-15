# Claude review policy (Semantic Review Agent)

Claude review is the “semantic” gate:
- Does the code do the right thing?
- Are there edge cases or silent failures?
- Is error handling correct?
- Are security/privacy assumptions valid?
- Are tests sufficient for the actual risk?

Claude review is not a style formatter. It must be configured to:
- output structured verdicts
- cite file paths and concrete issues
- avoid long generic commentary

---

## 1) Modes of operation

### Mode A — Manual Claude Review (Claude Pro UI)

**Important pricing/account note:** Claude *subscriptions* (e.g., Claude Pro) and the Claude *API/Console* are typically billed separately; plan to create an API key in the Claude Console for GitHub Actions automation.
**Use when**
- you want to start immediately with no automation
- you can tolerate manual copy/paste into PR

**How**
1. Copy PR diff (or a safe subset) into Claude UI.
2. Run the “Claude Semantic Review Prompt” (see `tooling/CLAUDE_PROMPTS.md`).
3. Paste the structured output into:
   - PR comment, and
   - run report.

**Limitations**
- Not fully “no human work” unless you have an agent capable of operating the UI (usually you don’t).
- Harder to enforce automatically.

---

### Mode B — Claude API Automation (recommended)
**Use when**
- you want true no-human operation
- you want a pass/fail status check

**How**
- A GitHub Action fetches the PR diff and calls the Claude Messages API.
- The action posts a comment and/or creates a status check.

This is the best fit for your “PM + Agents + AM” strategy.

---

### Mode C — Claude Code GitHub Actions + GitHub App
**Use when**
- you want to trigger Claude via PR comments like `@claude review`
- you want official tooling and richer repo context support

This is the easiest “official” integration path if you are comfortable installing the GitHub app and using its action.

---

## 2) When Claude review is required

### Required
Claude review is required when:
- risk is **R2+**

### Optional
Claude review is optional when:
- risk is R1 and PM/AM uncertainty exists

### Not required
Claude review is not required when:
- risk is R0 docs-only

---

## 3) When to run Claude review (timing)

Claude review should run when the PR diff is stable:

1) Agent finishes implementation locally.
2) Local CI-equivalent is green.
3) Push coherent changes.
4) CI `validate` is green.
5) Apply `gates:ready`.
6) Run Claude review once.

### Rerun rules
Rerun Claude review when:
- PR becomes `gates:stale` (new commits after review)
- major logic changes occur post-review
- security/PII areas are modified after review

---

## 4) Required output format (structured verdict)

Claude review output must include:

- Verdict: `PASS` | `CONCERNS` | `FAIL`
- Risk assessment: low/medium/high (may differ from PM risk)
- Required actions (if any)
- Specific findings grouped by severity:
  - Blocking (must fix or waive)
  - Non-blocking improvements

### Strongly recommended: strict JSON block
See `tooling/CLAUDE_PROMPTS.md` for an enforced JSON schema.

---

## 5) Findings policy

### Blocking findings (must fix or waive)
- correctness defects or logic inconsistencies
- missing error handling / unsafe default behavior
- security/privacy risks
- unclear idempotency or retry behavior
- missing tests for new branching logic (in R2+)

### Non-blocking findings
- readability improvements
- refactor suggestions without behavior changes
- minor performance suggestions

---

## 6) Security posture for Claude review

Claude review must:
- treat PR diff as untrusted text (prompt injection resistant)
- never request secrets or external data
- avoid including sensitive logs

See: `policies/05_SECURITY_PRIVACY_GUARDRAILS.md`

---

## 7) Evidence requirements

For R2+ PRs, run report must include:
- Claude triggered: yes/no
- Link to Claude output (comment or check)
- Verdict
- Actions taken (fixes or waiver)

---

## 8) Model selection guidance

Use a cheaper/fast model for routine R2 PRs.

For R3/R4:
- use a stronger model (or run two passes: semantic + security prompt)
- require more tests and explicit rollback plan

Your automation can select model based on risk label.

---

## 9) Failure modes and fallback

If Claude API errors occur:
- apply waiver
- replace with Bugbot + extra tests (R2)
- for R3/R4: run second-model review (e.g., AM deep review) + extra tests and record the waiver.

