# Active Workstreams

Last updated: 2025-12-30 (Wave B00)

**Current mode:** build (see `REHYDRATION_PACK/MODE.yaml`)  
Focus has shifted from “docs OS readiness” → **implementation with Cursor agents**.

---

## Recently completed (Foundation)
- Docs indexing + registries (doc registry, heading index)
- Rehydration pack automation + templates
- Policy + template hardening
- Doc hygiene cleanup
- GitHub + CI hardening (branch protection + deterministic regen)

---

## Active (Build)

### Stream B0 — Build kickoff + agent takeover (WAVE_B00)
- Ensure build mode is active in `MODE.yaml`
- Keep packs/status docs current
- Runbook parity with real GitHub settings

### Stream B1 — Sprint 0 Preflight (access + secrets inventory)
- Inventory required accounts/keys (AWS, Richpanel, email provider, shipping platform)
- Confirm “no tracking numbers” behavior (CR-001) and what fields are authoritative

### Stream B2 — Sprint 1 Infra baseline (IaC scaffolding)
- Stand up CDK project baseline + environments
- Define core resources (SQS, DynamoDB, Lambda skeletons) without requiring production credentials

---

## Blocking inputs (human)
- AWS account/credentials + target region(s)
- Richpanel API access + sandbox/staging details
- Shipping provider details (if ShipStation is used) and field mapping confirmations
