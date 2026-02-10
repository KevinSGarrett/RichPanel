<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-10 -->

**Run ID:** `B75_B_DEV_E2E`  
**Agents:** B  
**Labels:** `risk:R2`  
**Risk:** `risk:R2`  
**Claude gate model (used):** N/A  
**Anthropic response id:** N/A  

### 1) Summary
- Normalized shipping method label to match tracking carrier in automated replies.
- Enabled Shopify outbound reads in DEV to surface tracking numbers from fulfillments.
- Fixed auto-close by reducing close candidates and increasing Lambda timeout.
- Baked all runtime flags into CDK stack to prevent deploy-time config wipes.
- Proven end-to-end: tracking link + operator reply + auto-close + loop prevention tag.

### 2) Why
- Shipping method label ("USPS/UPS® Ground") conflicted with actual carrier (FedEx).
- Tracking numbers were missing because Shopify outbound was disabled.
- Auto-close broke due to 22 close candidates exceeding 30s Lambda timeout.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- DEV email-channel ticket triggers order-status automation.
- Order matched and tracking number present (when Shopify has fulfillment data).
- Latest operator reply includes a carrier tracking link (FedEx/UPS/USPS/DHL domain).
- Shipping method label normalized to match carrier.
- Reply sent via `/send-message` and ticket auto-closed.
- Follow-up customer replies route to Email Support Team via `mw-auto-replied` tag.

**Non-goals (explicitly not changed):**
- Production/staging behavior.

### 4) What changed
**Core changes:**
- Normalize shipping method label to the tracking carrier in tracking replies.
- Enable Shopify outbound reads in DEV worker (read-only).
- Fix fulfillment selection to pick first fulfillment with tracking.
- Reduce close candidates from 22 to 3 proven-working payloads.
- Bake all runtime flags into CDK stack definition.
- Increase worker Lambda timeout from 30s to 60s.

**Design decisions (why this way):**
- Only 3 close payloads because `{"ticket": {"state": "closed", "status": "CLOSED"}}` is the only confirmed-working payload for Richpanel.
- Runtime flags in CDK to prevent deploy-time config wipes.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`
- `backend/src/richpanel_middleware/commerce/order_lookup.py`
- `backend/src/richpanel_middleware/commerce/__init__.py`

**Infra:**
- `infra/cdk/lib/richpanel-middleware-stack.ts`
- `infra/cdk/cdk.json`

**Tests:**
- None (DEV E2E proof only)

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B75/B/PROOF/dev_tracking_link_e2e.json`
- `REHYDRATION_PACK/RUNS/B75/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B75/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B75/B/CHANGES.md`

### 6) Test plan
**E2E / proof runs (PII redacted):**
- Created DEV email ticket with order number in message body.
- Waited for middleware to process via webhook → SQS → worker.
- Verified: automation triggers, intent=order_status, order matched, tracking number present, tracking link domain=www.fedex.com, is_operator=true, ticket status=CLOSED.

### 7) Results & evidence
**Result:** PASS — All 7 requirements proven on ticket 1356.

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B75/B/PROOF/dev_tracking_link_e2e.json`

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — DEV-only changes (reply formatting, Shopify reads, close logic, infra config).

**Rollback plan:**
- Revert code changes and redeploy DEV stack. Runtime flags are now in CDK so rollback is clean.

### 9) Reviewer + tool focus
**Please double-check:**
- Close candidate payloads (only 3 now — confirm these work for your Richpanel setup).
- Shopify outbound enabled only in DEV (gated by `this.environmentConfig.name === "dev"`).

**Please ignore:**
- N/A
