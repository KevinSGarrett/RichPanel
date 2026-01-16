# Run report — PR Health Check section (template)

Copy this section into your agent run report.

---

## PR Health Check (required)

### CI
- **Local CI-equivalent run:** `python scripts/run_ci_checks.py --ci`
- **Result:** PASS/FAIL
- **Output snippet / log link:** ...
- **GitHub Actions run link:** ...

### Codecov
- **Codecov patch status:** PASS/FAIL/N/A
- **Codecov project status:** PASS/FAIL/N/A
- **Coverage issues identified:** ...
- **Action taken:** (tests added / waiver / N/A)

### Bugbot
- **Bugbot required:** yes/no
- **Bugbot triggered:** yes/no
- **Bugbot comment permalink:** ...
- **Findings summary:** ...
- **Action taken:** (fixed/false positive/waived)

### Claude review
- **Claude required:** yes/no
- **Claude triggered:** yes/no
- **Claude output link:** ...
- **Verdict:** PASS/CONCERNS/FAIL
- **Action taken:** (fixed/waived)

### E2E Proof (if applicable)
- **E2E required:** yes/no
- **Scenario(s) executed:** ...
- **Evidence folder/link:** ...
- **Outcome:** PASS/FAIL

### Waivers (if any)
- **Waiver used:** yes/no
- **Waiver text:** (paste)
- **Alternate evidence:** ...

