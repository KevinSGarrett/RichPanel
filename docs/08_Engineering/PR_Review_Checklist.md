# PR Review Checklist

**Status:** Canonical  
**Last Updated:** 2026-01-20

This checklist defines the **mandatory requirements** for all PRs before they can be merged. These requirements ensure quality, safety, and auditability.

---

## Required Labels

Every PR must have **exactly one** risk label:

- [ ] `risk:R0` — Docs-only changes
- [ ] `risk:R1` — Minor code changes, low risk
- [ ] `risk:R2` — Medium risk (new features, integrations)
- [ ] `risk:R3` — High risk (production automation, external APIs)
- [ ] `risk:R4` — Critical risk (security, data handling)

---

## Required Reviews

- [ ] **Claude Review** — Mandatory for all PRs
  - Claude gate label (`gate:claude`) is auto-applied
  - PR comment must include:
    - Anthropic Response ID (format: `msg_*`)
    - Token usage (input/output tokens)
    - Verdict: `CLAUDE_REVIEW: PASS` or `FAIL`
  - Gate uses risk-tiered models:
    - R0: Haiku 3.5
    - R1: Sonnet 4.5
    - R2/R3/R4: Opus 4.5

- [ ] **PR-Agent Advisory Review** — Auto-posted on all same-repo PRs (replaces deprecated Bugbot)
  - Runs automatically via `pull_request_target` (no manual trigger needed)
  - View output via `gh pr view <PR#> --comments`
  - If unavailable: document manual review in `RUN_REPORT.md`

---

## Required CI Checks

- [ ] **Unit Tests** — All tests must pass
- [ ] **Lint** — Ruff (advisory), Mypy (advisory), Black (advisory), compileall (blocking)
- [ ] **CI Checks** — `python scripts/run_ci_checks.py --ci` must pass
  - Rehydration pack validation
  - Docs registry validation
  - Doc hygiene checks
  - Plan sync validation
  - Protected delete checks

- [ ] **Codecov** — Coverage checks must pass or be acceptable
  - `codecov/patch` must meet the repo's current threshold (see the PR's status check)
  - `codecov/project` must not drop significantly from base branch
  - If unavailable: download `coverage-report` artifact and document

---

## Order Status Changes (Special Requirements)

If this PR touches **order status automation**, **order lookup logic**, or **Shopify/Richpanel integration for order data**:

- [ ] **OpenAI Evidence Required** — Attach proof JSON showing OpenAI usage
  - **Routing evidence:**
    - `openai.routing.llm_called=true`
    - `model`, `confidence`, `final_intent`, `response_id` (or `response_id_unavailable_reason`)
  - **Rewrite evidence:**
    - `openai.rewrite.rewrite_attempted=true`
    - `openai.rewrite.rewrite_applied=true` (or `fallback_used=true` + `error_class`)
  - **See:** `docs/08_Engineering/Order_Status_OpenAI_Contract.md`

- [ ] **E2E Proof (PASS_STRONG)** — Both scenarios required:
  - `order_status_tracking` (with tracking number/URL)
  - `order_status_no_tracking` (ETA-based)
  - Proof JSON must show:
    - Webhook accepted (HTTP 200/202)
    - DynamoDB records (idempotency, state, audit)
    - Ticket status changed to `resolved` / `closed`
    - Reply evidence (message_count delta > 0 OR last_message_source=middleware)
    - Middleware tags applied: `mw-auto-replied`, `mw-order-status-answered`
    - NO skip/escalation tags
    - PII-safe (ticket IDs hashed, paths redacted)

- [ ] **Follow-up Routing Verified (Optional but Recommended)**
  - Follow-up webhook sent after auto-reply
  - Routed to Email Support Team (no duplicate auto-reply)
  - Tags: `route-email-support-team`, `mw-skip-followup-after-auto-reply`

---

## Evidence Artifacts

- [ ] **Run Report** — `REHYDRATION_PACK/RUNS/<RUN_ID>/A/RUN_REPORT.md`
  - Summary of changes
  - CI output
  - Test results
  - PR-Agent findings (or manual review notes)
  - Codecov status

- [ ] **Test Matrix** — If applicable, E2E proof results
- [ ] **Docs Impact Map** — If docs changed

---

## Final Checks

- [ ] **All checks green** — Unit tests, lint, CI checks, Codecov, architecture boundaries, CodeQL, Claude gate
- [ ] **No placeholders** — No `???`, `TBD`, `WIP` in code or docs
- [ ] **No PII** — No raw customer emails, phone numbers, ticket IDs in PR body
- [ ] **Run artifacts complete** — All required files in `REHYDRATION_PACK/RUNS/<RUN_ID>/`
- [ ] **PR title score ≥95** — Using `07_PR_TITLE_SCORING_RUBRIC.md`
- [ ] **PR body score ≥95** (R0/R1) or ≥97 (R2/R3/R4) — Using `03_PR_DESCRIPTION_SCORING_RUBRIC.md`

---

## Merge Policy

- **Merge method:** Merge commit ONLY (no squash, no rebase)
- **Auto-merge:** Only enable after all checks are green
- **Command:**

```powershell
gh pr merge --auto --merge --delete-branch
```

---

## Related Documentation

- **PR Title Scoring:** `REHYDRATION_PACK/PR_DESCRIPTION/07_PR_TITLE_SCORING_RUBRIC.md`
- **PR Body Scoring:** `REHYDRATION_PACK/PR_DESCRIPTION/03_PR_DESCRIPTION_SCORING_RUBRIC.md`
- **CI Runbook:** `docs/08_Engineering/CI_and_Actions_Runbook.md`
- **Order Status OpenAI Contract:** `docs/08_Engineering/Order_Status_OpenAI_Contract.md`
- **Prod Read-Only Shadow Mode:** `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`

---

## Revision History

| Date       | Author        | Change                                     |
|------------|---------------|--------------------------------------------|
| 2026-01-20 | Cursor Agent  | Initial version (B48 documentation task)   |
