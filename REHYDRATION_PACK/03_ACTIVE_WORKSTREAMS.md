# Active Workstreams

Last updated: 2026-01-03 (Wave B06)

**Current mode:** build (see `REHYDRATION_PACK/MODE.yaml`)  
Focus is on **shipping functionality safely** (dev/staging green; prod gated).

---

## Recently completed (Foundation)
- Docs indexing + registries (doc registry, heading index)
- Rehydration pack automation + templates
- Policy + template hardening
- Doc hygiene cleanup
- GitHub + CI hardening (branch protection + deterministic regen)

---

## Active (Build)

### Stream B0 — Release discipline + evidence
- Keep rehydration/PM snapshots aligned to shipped reality (avoid “stale prompts”)
- Keep test evidence links current (dev/staging deploy + smoke)
- Maintain doc anti-drift (`verify_admin_logs_sync`)

### Stream B1 — Integrations (next)
- Shopify integration work (credentials, mapping, fallbacks)
- ShipStation integration work (if used) + field mapping confirmations
- Align integration behavior to CR-001 (delivery estimate only; no tracking)

### Stream B2 — Richpanel configuration + operator UX
- Document and implement the Richpanel-side configuration needed for stable operation
- Ensure operators can validate and safely toggle behavior (safe_mode / automation_enabled)

---

## Blocking inputs (human)
- AWS account/credentials + target region(s)
- Richpanel API access + sandbox/staging details
- Shipping provider details (if ShipStation is used) and field mapping confirmations
