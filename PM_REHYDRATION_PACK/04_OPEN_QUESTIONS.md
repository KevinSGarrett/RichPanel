# Meta Open Questions (Non-blocking)

Last updated: 2025-12-29 (Wave F13)

No blocking meta-questions right now.

Answered in Wave F06:
- Legacy duplicate folders are kept as **redirect stubs** (MOVED.md) rather than deleted.
- Plan checklist extraction is **automated** via `scripts/regen_plan_checklist.py`.

Next likely meta-decisions (later):
1) CI enforcement strategy for “no secrets in repo” (pre-commit + GitHub Actions).
2) Admin console auth approach (Cognito vs SSO/IdP).
3) Developer “one command” workflow (Makefile/task runner).

## CR-001 (No-tracking delivery estimates)
1) Exact Shopify/Richpanel shipping method strings for each bucket.
2) Pre-order ETA source-of-truth (field/tag/metafield/policy table).
3) Business-day calendar (Mon–Fri only vs holiday-aware) + timezone.
4) Richpanel: does "Resolved" reopen on customer reply?
