# Test Strategy and Matrix

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness) — **middleware + routing + FAQ automation**.

This document defines the **production-grade testing strategy** for the Richpanel middleware project.

It is designed to:
- prevent the *common issues* captured in `CommonIssues.zip` (loops, duplicates, spoofing, rate limits, missing identifiers, etc.)
- keep the LLM output **fail-closed** (schemas + policy gates) rather than “trusting” the model
- make releases predictable (staging → canary → gradual enablement)

---

## Quality goals (what “good” means)

### Safety (non-negotiable)
- No automation loops (no repeated auto-replies / re-triggers).
- No Tier 0 misses due to automation (chargebacks/disputes/legal/fraud always route to the correct queue).
- No private data disclosure without **deterministic match** (Tier 2 verifier + policy gates).

### Reliability
- Ingress webhook ACK time is fast (so Richpanel does not retry or time out).
- Duplicate webhook deliveries do not produce duplicate actions (idempotency at event + action layer).
- Backlog drains safely without rate-limit storms.

### Correctness
- Primary intent routing is correct at acceptable thresholds.
- FAQ automation only triggers when policy gates allow it.
- Templates render correctly and include only allowed variables.

### Operability
- Logs/metrics/traces allow debugging without exposing PII.
- Kill-switch and safe-mode work at runtime.

---

## Test pyramid (how we structure tests)

We use a layered approach so most failures are caught early (cheap tests) and only a smaller set requires staging/manual QA.

1) **Unit tests** (fast, deterministic)
   - Policy engine gates (Tier rules, multi-intent precedence, deterministic-match gating)
   - Template rendering + variable handling
   - Redaction utilities and “no PII in logs” invariants
   - Idempotency key generation + de-dup windows

2) **Component tests** (still fast; dependencies mocked)
   - Ingress handler: payload validation → enqueue
   - Worker handler: decision pipeline → action planner
   - Rate-limit handling logic (429 + Retry-After)
   - DLQ behavior for poisoned messages

3) **Contract tests** (schema + API shape)
   - JSON schema validation for:
     - inbound webhook payload (our middleware contract)
     - LLM outputs (`mw_decision_v1`, `mw_tier2_verifier_v1`)
     - observability events (`mw_observability_event_v1`)
   - Richpanel / Shopify API response shape validation against recorded fixtures (sanitized)

4) **Integration tests** (real HTTP calls to stubs or sandbox)
   - “Webhook → queue → worker → simulated Richpanel write”
   - verify retries, idempotency, and no double-sends
   - verify that unsafe LLM outputs are downgraded by policy engine

5) **End-to-end tests** (staging / production-like)
   - minimal set of real flows:
     - routing tags applied correctly
     - safe-mode disables automation
     - Tier 2 order status only with deterministic match
   - runs with “dry-run” toggles if staging Richpanel is not available

6) **LLM eval tests** (offline)
   - golden set eval gates (Wave 04)
   - regression gates in CI (Wave 08/09 alignment)

7) **Load / soak tests**
   - validate queue backpressure and vendor-rate-limit behaviors (Wave 07/09 alignment)

8) **Security tests**
   - webhook auth negative tests (spoofing)
   - secret scanning + dependency scanning gates (Wave 06 alignment)

---

## Test matrix (what runs when)

| Layer | Examples | Runs | Blocks merge? | Blocks release? | Notes |
|---|---|---:|---:|---:|---|
| Unit | policy gates, templates, redaction | every PR | ✅ | ✅ | fastest + highest ROI |
| Component | lambda handlers with mocks | every PR | ✅ | ✅ | validates glue code |
| Contract | JSON schema checks, API fixtures | every PR | ✅ | ✅ | prevents “silent drift” |
| Integration | webhook→queue→actions (stubbed Richpanel) | nightly + before release | 🟡 (recommended) | ✅ | can be slower; worth it |
| E2E staging | real-ish flows + safe-mode | before release | — | ✅ | minimal set; high signal |
| LLM eval | golden set + regression gates | prompt/model changes + nightly | ✅ (for prompt changes) | ✅ | uses Wave 04 gates |
| Load/soak | peak + spike + chaos | before major release | — | 🟡 (recommended) | required before large rollout |
| Security | spoofing tests, scans | every PR + before release | ✅ | ✅ | align Wave 06 |

Legend:
- ✅ required gate
- 🟡 recommended gate (promote to required as we mature)

---

## “Common issues” coverage mapping (must-have)

These are the highest-risk issues from `CommonIssues.zip` and the minimum test coverage required.

| Common issue | How we test it |
|---|---|
| Automation loops | unit + integration: ensure `mw-routing-applied` / de-dup windows; ensure no trigger on our own reply |
| Webhook spoofing | contract + security: invalid token rejected; replay attack rejected by timestamp/nonce (if used) |
| Duplicate events | unit + integration: same event id produces no second action |
| ACK fast timeouts | component: ingress handler always returns 2xx quickly and queues work |
| Rate limits | integration + load: simulate 429 + Retry-After; verify backoff + queue growth not failure |
| Ticket state conflicts | integration: simulate concurrent updates; ensure last-write rules and no thrash |
| Team mapping drift | contract: missing team/tag falls back to safe routing |
| Confidence calibration | LLM eval: threshold changes require eval gates |
| Order status pitfalls | integration + manual QA: no deterministic match → “ask order #”; never disclose address |
| Attachments / non-text | unit + integration: non-text routes safe; no OCR by default; attachment size safeguards |

---

## Environments used for testing

- **Dev:** fastest feedback, uses stubs/mocks. No customer data.
- **Staging:** production-like config, safe-mode defaults on. Minimal real integrations.
- **Prod:** gated rollout (canary + feature flags). No testing against real customers unless explicitly approved.

Environment details live in: `docs/09_Deployment_Operations/Environments.md`.

---

## Release gates (summary)

Before enabling automation in production:
- Schema gates pass (LLM outputs + ingress)
- Tier 0 safety gates pass (no FN)
- Kill switch verified (safe_mode + automation_enabled)
- Smoke tests pass in staging
- Rollback plan is ready and rehearsed (at least tabletop)

See:
- `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`
- `docs/09_Deployment_Operations/Release_and_Rollback.md`
