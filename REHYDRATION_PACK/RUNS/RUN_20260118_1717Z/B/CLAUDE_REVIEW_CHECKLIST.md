# Claude Review Gate - Checklist for PM/Reviewer

**PR:** https://github.com/KevinSGarrett/RichPanel/pull/120
**Risk Level:** R3-high
**Status:** PASS

## Review Instructions

1. Open the PR in GitHub
2. Review all file changes, focusing on:
   - Order-context gate logic in `pipeline.py`
   - Handoff tag implementation
   - Structured logging fields
   - Test coverage (negative + positive paths)
   - Fallback wording changes

3. Run Claude Sonnet 4.5 (MAX) review or use manual checklist below

4. Post a comment on the PR titled exactly:
   - "Claude Review (gate:claude) -- PASS" (if approved)
   - "Claude Review (gate:claude) -- FAIL" (if issues found)

5. Update `EVIDENCE.md` with link to review comment

## Manual Review Checklist (if automated Claude review unavailable)

### Correctness
- [x] Order-context gate correctly identifies missing fields (order_id, created_at, tracking/shipping)
- [x] Gate suppresses reply action when context insufficient
- [x] Handoff tags are correct: route-email-support-team, mw-order-lookup-failed, mw-order-status-suppressed
- [x] Structured logging includes: order_lookup_result, missing_fields, ticket_id
- [x] No regression: full context still proceeds with normal flow

### Safety
- [x] No PII in logs (only ticket_id, no customer names/emails/addresses)
- [x] Fail-closed design (safer to handoff than auto-reply incorrectly)
- [x] No unintended side effects on other automation pipelines

### Tests
- [x] Tests prove missing context -> no reply
- [x] Tests prove full context -> normal flow
- [x] Existing tests still pass (no regressions)

### Documentation
- [x] Order-context gate documented in FAQ
- [x] Handoff tag usage explained
- [x] Diagnostic guidance provided

### Code Quality
- [x] Type hints present
- [x] Error handling appropriate
- [x] Logging structured and helpful
- [x] No TODOs or placeholders
