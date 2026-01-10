# Run Meta

- RUN_ID: $runId
- Mode: build
- Objective: Implement audit remediation semantics (reply-after-close routing + status read-before-write + follow-up routing policy) without new Richpanel APIs.
- Stop conditions: Unit tests pass; outbound remains fail-closed/PII-safe; docs updated; run report completed.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: python scripts/verify_rehydration_pack.py (build mode)
