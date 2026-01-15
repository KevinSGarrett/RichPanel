# Quality Gates and Risk Labels — Quick Reference

**Date:** 2026-01-15  
**Status:** Canonical  
**Owner:** Engineering + PM

This is a concise reference card for the RichPanel NewWorkflows quality gate system. For detailed procedures, see [CI and Actions Runbook](./CI_and_Actions_Runbook.md).

---

## 1) Risk-based quality philosophy

**Core principle:** Not all changes carry equal risk. We run expensive quality gates (Bugbot, Claude, E2E proof) only when the risk level justifies the cost.

**Every PR must have exactly one risk label** that determines which gates are required.

---

## 2) Risk label taxonomy (R0–R4)

### R0 — `risk:R0-docs` (Docs-only / non-functional)

**What it means:**
- Documentation edits, markdown formatting, typos, README updates
- No production code changes
- No functional impact

**Required gates:**
- CI: Optional (if repo requires it, must pass)
- Codecov: Not required
- Bugbot: Not required
- Claude: Not required
- E2E proof: Not required

**Examples:**
- Fixing typos in `docs/`
- Updating README
- Formatting markdown files

---

### R1 — `risk:R1-low` (Low risk, localized changes)

**What it means:**
- Small, localized changes
- No production behavior changes or external side effects
- No security/PII impact
- Low blast radius, easy rollback

**Required gates:**
- CI: Required (`validate` must pass)
- Codecov: Advisory (not blocking unless coverage materially degrades)
- Bugbot: Optional (required if critical zones touched)
- Claude: Optional (not required unless uncertainty exists)
- E2E proof: Not required

**Examples:**
- Small refactor with no behavior change
- Non-critical helper bugfix
- Logging message tweaks (no data fields changed)
- Small UI copy changes

**Note:** If change touches critical zones (auth, PII, outbound, persistence), automatically upgrade to R2.

---

### R2 — `risk:R2-medium` (Behavior changes, non-trivial logic)

**What it means:**
- Behavior changes or non-trivial logic modifications
- New code paths, branching, retries, parsing, transformations
- Integration changes affecting correctness
- Moderate blast radius

**Required gates:**
- CI: Required (`validate` must pass)
- Codecov: **Patch coverage required** (≥50% or justification)
- Bugbot: **Required** (run once on stable diff)
- Claude: **Required** (semantic review once on stable diff)
- E2E proof: Conditional (required if change touches outbound/automation)

**Examples:**
- Modifying automation routing logic
- Changing classifier thresholds
- Adding new endpoint/handler
- Changing caching keys or invalidation
- Schema changes (even additive)

**Evidence requirements:**
- Bugbot comment link + triage summary
- Codecov patch status (or waiver with justification)
- Claude review verdict + link (or manual review if API unavailable)

---

### R3 — `risk:R3-high` (High blast radius, security-sensitive)

**What it means:**
- High blast radius or error-prone domains
- Security/privacy-sensitive changes
- Outbound network behavior changes
- Changes that could silently degrade correctness

**Required gates:**
- CI: Required (`validate` must pass)
- Codecov: **Patch + project thresholds required**
- Bugbot: **Required** (rerun if significant changes after initial review)
- Claude: **Required** (with security-focused prompt; rerun if stale)
- E2E proof: **Required if change touches outbound/network/automation**

**Examples:**
- Auth, token validation, permissions, session handling
- PII redaction/logging pipelines
- Webhooks / inbound automation triggers
- Payment/order status logic
- Background job semantics
- Infra changes affecting runtime behavior

**Evidence requirements:**
- All R2 evidence, plus:
  - Explicit security review notes
  - E2E proof with real environment validation
  - Staleness checks (re-run gates if commits land after review)

---

### R4 — `risk:R4-critical` (Production emergency, security incident)

**What it means:**
- Production emergency / security incident / compliance-critical change
- Requires strongest gates and strict documentation

**Required gates:**
- CI: Required (`validate` must pass)
- Codecov: **Patch + project thresholds required**
- Bugbot: **Required**
- Claude: **Required + double-review strategy** (Claude + independent LLM review, e.g., AM deep review)
- E2E proof: **Required**
- **Additional:** Explicit rollback plan + post-merge verification checklist

**Examples:**
- Actively exploited vulnerability fix
- Incident mitigation in production
- Key rotation or emergency secret changes
- Data corruption fixes

**Evidence requirements:**
- All R3 evidence, plus:
  - Double-review outputs (Claude + AM or second reviewer)
  - Documented rollback plan
  - Post-merge verification checklist
  - Incident tracking link

---

## 3) Critical zones (auto-upgrade to R2 minimum)

If any file under these areas changes, **minimum risk is R2** (often R3):

- `backend/src/` (all backend runtime code)
- Automation or routing logic
- Webhook handlers
- Anything touching:
  - Secrets / credentials
  - Authentication / authorization
  - PII handling / redaction
  - Outbound HTTP requests
  - Persistence / data migration

**If unsure, classify as R2.**

---

## 4) Gate lifecycle (PR workflow states)

### Gate state labels

Use these optional labels to track gate progress:

- **`gates:ready`** — PR is stable (CI green, diff coherent) and ready to run heavy gates
- **`gates:running`** — Gate workflows currently in-flight
- **`gates:passed`** — Required gates completed successfully for current PR state
- **`gates:stale`** — New commits landed after gates ran; must re-run before merge

### Staleness rule (critical for AI-only workflow)

**If a PR receives new commits after:**
- Bugbot review output, or
- Claude review output, or
- `gates:passed` label applied

**Then gates become stale.**

The PR must:
1. Have `gates:stale` label applied
2. Remove `gates:passed` label
3. Re-run required gates before merge

This ensures "approved" means "approved for this exact code."

---

## 5) Two-phase workflow (cost control)

### Phase A: Build & stabilize (local iteration)
- Agent iterates locally
- Runs `python scripts/run_ci_checks.py --ci` until green
- Commits locally as needed
- **Only pushes to GitHub when diff is coherent** (reduces CI/Codecov runs)

### Phase B: Gate execution (PR-level, once per stable state)
- When CI is green and PR is stable: apply `gates:ready` label
- Heavy gates run **once per stable PR state:**
  - Bugbot (if required by risk level)
  - Claude review (if required by risk level)
  - Codecov gating (if required by risk level)
- **Avoids running expensive AI reviews on every micro-commit**

---

## 6) Evidence requirements (per risk level)

### R0 / R1 evidence
- PR template filled
- CI link (if CI ran)
- Local CI-equivalent run log snippet (recommended)

### R2+ evidence
- Everything above, plus:
  - **Bugbot:** Comment link + triage summary (findings + resolutions, or "no findings")
  - **Codecov:** Patch/project status summary (or waiver with justification)
  - **Claude:** Review verdict + link (or manual review documentation if API unavailable)
  - **E2E:** Evidence folder + logs + outcome (if required)

### R3 / R4 additional evidence
- Explicit rollback plan
- Post-merge monitoring/verification plan
- (R4 only) Double-review outputs

**No placeholders allowed** in run reports or PR descriptions:
- No `<FILL_ME>`
- No `TODO`
- No `TBD`

---

## 7) Gate reference matrix

| Risk | CI | Local CI-equiv | Codecov | Bugbot | Claude | E2E |
|------|----|--------------------|---------|--------|--------|-----|
| R0 docs | Optional* | Optional* | Not required | Not required | Not required | Not required |
| R1 low | Required | Required | Advisory | Optional** | Optional | Not required |
| R2 med | Required | Required | **Patch required** | **Required** | **Required** | Conditional |
| R3 high | Required | Required | **Patch + project** | **Required (stale-rerun)** | **Required (security prompt, stale-rerun)** | **Required if outbound/automation** |
| R4 critical | Required | Required | **Patch + project** | **Required** | **Required + double-review** | **Required** |

\* R0: If CI is mandatory due to repo settings, it still must pass, but Codecov/Bugbot/Claude are waived by default.  
\** R1: Bugbot becomes required if critical zones are touched.

---

## 8) Quick CLI reference

```powershell
# Apply risk label (required for every PR)
gh pr edit <PR#> --add-label "risk:R2-medium"

# Trigger Bugbot (R2+)
gh pr comment <PR#> -b '@cursor review'

# View Bugbot output
gh pr view <PR#> --comments

# Check Codecov status (R2+)
gh pr checks <PR#>

# Trigger Claude review (R2+, if supported)
gh pr comment <PR#> -b '@claude review'
# Fallback: manual review if Anthropic key unavailable
gh pr diff <PR#> > pr_diff.txt
# Review manually, document in run report, apply waiver:active label

# Apply gate status labels
gh pr edit <PR#> --add-label "gates:ready"
gh pr edit <PR#> --add-label "gates:passed"
```

---

## 9) Waivers and exceptions

**Waivers are allowed** when external services fail (Codecov outage, Bugbot quota exhausted, Claude API errors).

**Waiver rules:**
1. Waivers are **time-bounded** and **explicit**
2. Waivers require alternate evidence or alternate gates
   - Example: Replace Bugbot with Claude security review + extra tests
3. Waivers must be recorded in:
   - PR description (Waiver section)
   - Run report (Findings/Waiver section)
4. Apply label: `waiver:active`

**Example waiver documentation:**
```
## Waiver

**Gate:** Bugbot  
**Reason:** Bugbot quota exhausted  
**Alternate evidence:** Performed manual code review focusing on edge cases,
error handling, and integration correctness. No blocking issues found.
See run report Section 5 for detailed findings.  
**Approved by:** PM (recorded in cycle notes)
```

---

## 10) Merge readiness rule

**A PR is merge-ready only when:**

1. **Risk declared:** Exactly one risk label applied (R0–R4)
2. **CI green:** Required GitHub checks passing
3. **Gates satisfied:** All required gates for risk level completed and non-stale
4. **Evidence complete:** Run report has no placeholders; all required links/proof present
5. **Waivers documented:** Any waivers explicitly recorded with justification
6. **AM score ≥ 95:** (if using AM review process) and references all evidence

**Do not merge until all conditions are met.**

---

## 11) Related documents

- [CI and Actions Runbook](./CI_and_Actions_Runbook.md) — Detailed procedures for CI, Bugbot, Codecov, Claude, E2E
- PM_REHYDRATION_PACK/NewWorkflows/policies/ — Full policy set
  - `02_GATE_MATRIX.md` — Complete gate requirements and evidence checklists
  - `01_RISK_CLASSIFICATION.md` — Risk scoring algorithm and examples
  - `07_LABEL_TAXONOMY.md` — Complete label reference
  - `04_EVIDENCE_AND_AUDIT.md` — Evidence formatting and audit requirements

---

**Remember:** This is an AI-only workflow. Gates are our safety net for correctness and security. Always apply the appropriate risk label and complete required gates before merge.
