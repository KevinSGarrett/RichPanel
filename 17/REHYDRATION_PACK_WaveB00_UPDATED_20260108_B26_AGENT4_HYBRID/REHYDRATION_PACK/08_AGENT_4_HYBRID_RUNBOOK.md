# Agent 4 hybrid runbook (DEV → STAGING proof)

Last updated: **2026-01-08**  
Purpose: Make Agent 4 (Human) a **hybrid workflow** where Cursor Agents do the repo/code heavy lifting **before and after** the human proof run.

This runbook is optimized for:
- minimal “core file” editing by humans
- repeatable DEV proof runs
- clean evidence capture
- staging parity once DEV is proven

---

## What is already DONE (from Agent 4 closeout)

From `Richpanel_Middleware_Agent_4_Dev_Runbook_Checklist_Close.md`, DEV has:

- DEV stack deployed and reachable (ingress + worker)
- Richpanel webhook configured to hit ingress
- Inbound webhook processing verified (idempotency/state/audit writes)
- Routing + order-status planning verified offline-first
- Known operational issues documented + mitigations recorded

Important: **Two blockers mentioned in the closeout are now fixed in main**:
- `missing_draft_reply` root cause (planner now always generates a safe fallback draft) — merged via PR #54.
- DynamoDB float crash (floats sanitized → Decimal) — merged via PR #60.

If DEV is still showing those failures, it almost certainly means **DEV Lambda has not been redeployed from latest main**.

---

## Hybrid workflow overview

### Phase 0 — Cursor preflight (agents)
Goal: make the proof run “boring” for the human.

Cursor Agents should deliver:
1) Any remaining code fixes required for DEV proof (PRs merged, CI green)
2) Runbook updates that reflect true shipped behavior
3) Optional tooling to make evidence capture fast

### Phase 1 — Human execution (Agent 4)
Goal: run a real DEV test ticket end-to-end, capture evidence, then revert flags.

### Phase 2 — Cursor postflight (agents)
Goal: encode learnings into docs/checklists + prep staging rollout.

---

## Phase 0 — Cursor agent preflight checklist

### 0.1 Pull latest main + verify merged fixes are present
- Confirm PR #54 and #60 are merged into main.
- Redeploy DEV (via workflow) so Lambda code includes them.

### 0.2 Ensure runtime flags are controllable
We need:
- `safe_mode = false`
- `automation_enabled = true`
for the proof run.

Preferred: use GitHub Actions **Set Runtime Flags** workflow (OIDC role).
If the workflow fails due to SCP/permissions, open a task to add an **env-var fallback** (Cursor code change) so Agent 4 can toggle via Lambda environment variables.

### 0.3 Ensure outbound prerequisites are in place
For outbound order-status reply+resolve we need:
- secrets readable by the worker (Secrets Manager permissions)
- outbound flag enabled (RICHPANEL_OUTBOUND_ENABLED)
- network allowed (the worker sets allow_network = outbound_enabled)
- safe_mode false + automation_enabled true

### 0.4 Optional but recommended: persist outbound results
Right now outbound is logged, but DEV proof is easier if outbound results are also persisted in Dynamo state/audit (without reply bodies).

---

## Phase 1 — Agent 4 (Human) DEV proof run checklist

### 1.0 Preconditions (DEV)
- Latest main deployed to DEV
- Secrets seeded (Richpanel + Shopify + ShipStation if used; OpenAI optional for order-status proof)
- Richpanel webhook token header configured (no secret pasted into docs)
- Runtime flags: safe_mode false, automation_enabled true
- Outbound enabled: RICHPANEL_OUTBOUND_ENABLED=true

### 1.1 Trigger the proof ticket
Create a real Richpanel ticket (DEV mailbox/channel) with a unique marker, e.g.:
- Subject/body: `mwtest dev proof where is my order?`

Record:
- Richpanel ticket ID (conversation_id)
- Timestamp (UTC)

### 1.2 Verify inbound processing
CloudWatch (worker logs) should show:
- event received
- routing decision
- order_status_draft_reply planned

Dynamo should show:
- idempotency record written
- state record written
- audit record written

### 1.3 Verify outbound automation
Expected outcome (when outbound enabled):
- Public reply posted to the ticket
- Ticket status set to **resolved**
- Tag applied: `mw-auto-replied`
- (If routing tags outbound enabled) tags applied like `mw-intent-*` + `mw-routing-applied`

### 1.4 Capture evidence (minimum set)
Save:
- Richpanel ticket screenshot (showing reply + resolved + tags)
- CloudWatch log excerpt around the send (ensure no secrets)
- Dynamo state + audit JSON (redact any PII if present)

### 1.5 Revert flags (important)
After proof:
- turn outbound OFF (RICHPANEL_OUTBOUND_ENABLED=false)
- keep safe_mode/automation_enabled in preferred default (your call, but safest is safe_mode=true, automation_enabled=false outside of test windows)

---

## Phase 2 — Cursor postflight checklist

- Update Agent 4 runbook(s) with any gotchas encountered
- Update MASTER_CHECKLIST status signals (done/in progress/pending)
- Ensure GITHUB_STATE.md reflects:
  - what PRs merged
  - what was deployed to DEV
  - what remains for staging
- If staging is next: prepare a staging proof checklist mirroring DEV

---

## “Next checklist items” for Agent 4

**Agent 4 (Human) next actions:**
1) Confirm DEV is deployed from latest main (post-PR #54 + #60).
2) Seed secrets via workflow.
3) Use workflow (preferred) to set runtime flags: safe_mode=false, automation_enabled=true.
4) Enable outbound (RICHPANEL_OUTBOUND_ENABLED=true) for a short window.
5) Run the DEV proof ticket and capture evidence.
6) Turn outbound OFF again.
7) Repeat steps 1–6 in STAGING once DEV proof is clean.

**Cursor agents’ supporting actions:**
A) Add outbound-result persistence to state/audit (no reply bodies).  
B) Add a “proof run evidence checklist” doc and link it from CURRENT_STATE.  
C) If runtime flags cannot be toggled due to org policies: implement env-var fallback for kill switches (safe_mode/automation_enabled) with explicit precedence rules + tests.

