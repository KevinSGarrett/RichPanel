# Cursor Run Output Requirements

Last updated: 2025-12-23

Every Cursor agent run must output:

1) **Summary**
- Tickets completed (IDs)
- Files changed / added
- How to run tests
- Any deviations from ticket scope (and why)

2) **Evidence**
- Test output (unit/integration)
- Any screenshots (PII redacted)
- Links to produced artifacts (metrics, CSVs, etc.)

3) **Safety checks**
- Confirm no secrets were added to repo
- Confirm PII redaction rules are followed
- Confirm kill switch works (if the run touches automation)

4) **Next steps**
- Which tickets are unblocked now
- Which tickets remain blocked and why

The agent should include an updated project folder ZIP for the PM to review.
