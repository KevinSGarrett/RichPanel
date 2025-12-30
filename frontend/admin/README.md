# Admin Console (Placeholder)

**Status:** placeholder (planning only)

Recommended tech (non-binding):
- Next.js (TypeScript)
- Hosted on CloudFront + S3 or Vercel (later decision)
- Auth via Cognito / SSO (later decision)

## Planned pages
- Dashboard: volume, routing intents, confidence distribution
- Run history: per-run summaries (from `REHYDRATION_PACK/RUNS/`)
- Config: view effective thresholds / toggles (read-only first)

## Notes
We will not build this until:
1) routing + gating pipeline is stable
2) logging/audit schema is finalized (redacted)
