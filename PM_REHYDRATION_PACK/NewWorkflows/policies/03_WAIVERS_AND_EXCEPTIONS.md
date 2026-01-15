# Waivers and exceptions policy

Waivers exist because:
- external services go down (Codecov outage, Claude API outage, Bugbot quota)
- some changes are not testable in the normal way (e.g., CI infra-only)
- extremely small changes should not incur heavy gate costs

But waivers are also a risk. This policy keeps waivers controlled.

---

## 1) What a waiver is (and is not)

A waiver **is**:
- a documented exception to a specific gate requirement
- time-bounded
- tied to a PR and `RUN_ID`
- paired with alternate evidence

A waiver **is not**:
- “we didn’t feel like running the gate”
- “we forgot”
- “we plan to do it later” (no async promises)

---

## 2) When waivers are allowed

### Allowed reasons
- **External outage**: service is down or returning errors
- **Quota/rate limit**: Bugbot or Claude API quota exhausted
- **Security limitation**: cannot safely expose code or diffs to an external service
- **Non-applicability**: gate does not apply (docs-only)
- **Temporary migration**: transitional state explicitly approved by PM

### Not allowed
- bypassing R3/R4 gates without alternate evidence
- bypassing security/PII-related gates in security-sensitive PRs

---

## 3) Waiver levels

### Level 1 waiver (low impact)
- Applies to R0/R1 only
- Example: skip Bugbot on doc-only PR

### Level 2 waiver (moderate)
- Applies to R2 with justification
- Must include alternate evidence:
  - Claude review instead of Bugbot, or
  - extra tests instead of Codecov, etc.

### Level 3 waiver (high)
- Applies to R3/R4
- Requires:
  - explicit rollback plan
  - enhanced evidence (E2E, additional tests, or second-model review)
  - explicit PM decision recorded

---

## 4) Required waiver template

Copy from `templates/WAIVER_TEMPLATE.md`.

At minimum, waiver text must include:

- Gate waived (Bugbot / Codecov / Claude / E2E)
- Reason (outage/quota/non-applicable/etc.)
- Risk level
- Alternate evidence performed
- Expiration (time or PR scope)
- Follow-up action (if any)

---

## 5) Where waivers must be recorded

1. In PR description (Waivers section)
2. In run report (Findings/Waivers section)
3. Optional: in Progress Log entry for that RUN_ID (if your governance requires it)

---

## 6) Waiver expiration and cleanup

A waiver expires automatically when:
- the PR merges, or
- the blocking condition resolves and the PR is updated

If a waiver was used due to outage/quota:
- future PRs should revert to normal gates when service returns

---

## 7) AM scoring rule

If a required gate is missing and there is:
- no waiver, or
- waiver is incomplete / missing alternate evidence

Then AM score must be **< 95**.

