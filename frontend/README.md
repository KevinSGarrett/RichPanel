# Frontend (Planned)

We are planning a lightweight **admin / ops console**.
This is **not required** for v1 routing + FAQ automation launch, but we include a skeleton so:
- the repo has a clear “home” for UI work
- later waves can add it without restructuring

## Likely v1 scope (later wave)
- view last N middleware decisions (redacted)
- view routing distribution and confidence buckets
- view “automation enabled” + kill switch state
- manage allowlists / thresholds (if we decide to expose these)

## Security
- No customer PII in the UI (redacted views only)
- Auth via your chosen IdP / AWS Cognito (later decision)

See: `frontend/admin/README.md`
