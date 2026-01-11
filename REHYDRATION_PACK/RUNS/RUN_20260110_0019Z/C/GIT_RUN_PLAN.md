# Git Run Plan

**Run ID:** $runId  
**Agent:** C  
**Date:** 2026-01-10

## Plan
- Implement Richpanel ticket metadata read helper.
- Enforce outbound read-before-write + reply-after-close skip + follow-up routing policy.
- Add focused unit tests and update docs.
- Open PR and enable auto-merge.

## Guardrails
- Fail-closed: if ticket state cannot be determined, do not auto-reply.
- PII-safe: never log ticket bodies or customer profile fields.
