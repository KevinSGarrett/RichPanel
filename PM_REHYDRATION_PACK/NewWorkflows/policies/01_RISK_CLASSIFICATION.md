# Risk classification policy

Risk classification exists so we can:

- keep the repo safe and continuously shippable
- avoid wasting Bugbot/Codecov/Claude cycles on tiny changes
- make enforcement machine-checkable (labels → automation)

This policy defines **risk levels**, **how to decide**, and the **label taxonomy**.

---

## 1) Risk levels

### R0 — Docs-only / Non-functional
**Examples**
- docs edits only
- comment-only changes
- markdown formatting
- typos

**Typical touched paths**
- `docs/**`
- `README.md`
- `qa/test_evidence/README.md`

**Default gates**
- CI may be skipped if repo supports it; otherwise pass `validate`
- No Bugbot, no Claude, Codecov not required

---

### R1 — Low
**Definition**
- Small, localized change
- No production behavior changes or external side effects
- No security/PII impact
- Low blast radius and easy rollback

**Examples**
- small refactor with no behavior change
- bugfix in non-critical helper
- logging message tweaks (no data fields changed)
- small UI copy changes (if applicable)

**Default gates**
- CI `validate` required
- Codecov: advisory unless coverage changes materially
- Bugbot: optional (required if touching “critical zones”)
- Claude: not required (optional if uncertainty)

---

### R2 — Medium
**Definition**
- Behavior changes or non-trivial logic changes
- Any new code paths, branching, retries, parsing, or transformations
- Integration changes that could affect correctness
- Moderate blast radius

**Examples**
- modifying automation routing logic
- changing classifier thresholds
- adding a new endpoint/handler
- changing caching keys or invalidation
- schema changes (even additive)

**Default gates**
- CI `validate` required
- Codecov patch must pass (or waiver)
- Bugbot required once on stable diff (or waiver)
- Claude semantic review required once on stable diff (or waiver)

---

### R3 — High
**Definition**
- High blast radius changes or error-prone domains
- Any security/privacy-sensitive changes
- Any outbound network behavior changes
- Any change that could silently degrade correctness

**Examples**
- changes to auth, token validation, permissions, session handling
- PII redaction/logging pipelines
- webhooks / inbound automation triggers
- payment/order status logic
- background job semantics
- infra changes that affect runtime behavior

**Default gates**
- CI `validate` required
- Codecov patch + (recommended) project thresholds must pass
- Bugbot required (rerun if significant changes occur after review)
- Claude semantic review required (plus security-focused prompt)
- E2E proof required if the change touches outbound/network or automation behavior

---

### R4 — Critical
**Definition**
- Production emergency / security incident / compliance-critical change
- Requires the strongest gates and strict documentation

**Examples**
- actively exploited vulnerability fix
- incident mitigation in production
- key rotation or emergency secret changes
- data corruption fixes

**Default gates**
- All R3 gates, plus:
  - double-review strategy (Claude + independent LLM review, e.g., AM deep review)
  - explicit rollback + monitoring plan
  - post-merge verification checklist

---

## 2) “Critical zones” that upgrade risk automatically

If any file under these areas changes, minimum risk is **R2** (often R3):

- `backend/**` or server runtime code
- automation or routing logic
- webhook handlers
- anything that touches:
  - secrets
  - auth
  - PII handling
  - outbound requests
  - persistence/data migration

If unsure: classify as **R2**.

---

## 3) How PM assigns risk (algorithm)

PM must classify risk using:

1. **Impact**: what user/business behavior changes?
2. **Blast radius**: how many flows depend on this?
3. **Reversibility**: is rollback safe and easy?
4. **Observability**: will failure be obvious or silent?
5. **Security/PII**: any exposure risk?

A simple scoring system:

- Impact: 0–3
- Blast radius: 0–3
- Reversibility: 0–2 (harder = higher score)
- Observability: 0–2 (harder to detect = higher score)
- Security/PII: 0–5

**Mapping**
- 0–2 → R0/R1
- 3–6 → R2
- 7–10 → R3
- 11+ → R4

---

## 4) Labels (machine-enforceable)

Every PR must include exactly one risk label:

- `risk:R0-docs`
- `risk:R1-low`
- `risk:R2-medium`
- `risk:R3-high`
- `risk:R4-critical`

Optional labels (recommended):
- `gates:ready` — PR is stable and ready to run heavy gates
- `gates:stale` — new commits landed after gates ran
- `gates:passed` — required gates completed for current PR state
- `waiver:active` — waiver applied (must have waiver text)

See: `policies/07_LABEL_TAXONOMY.md`

---

## 5) Staleness rule (prevents “reviewed, then changed”)

If a PR receives new commits after:
- Bugbot review comment, or
- Claude review output, or
- “gates:passed” label

Then gates become **stale**. The PR must return to `gates:stale` until re-run.

This rule is essential for AI-only workflows, where “approved” must mean “approved for this exact code”.

---

## 6) Examples

### Example A — doc-only typo fix
- Risk: `risk:R0-docs`
- Gates: CI optional, no Bugbot/Claude, Codecov ignored

### Example B — adjust a parsing helper
- Risk: `risk:R1-low` (or `risk:R2-medium` if parsing affects routing)
- Gates: CI required; Bugbot optional; Codecov advisory; Claude optional

### Example C — change order status automation logic
- Risk: `risk:R3-high`
- Gates: CI + Codecov + Bugbot + Claude + E2E proof required

