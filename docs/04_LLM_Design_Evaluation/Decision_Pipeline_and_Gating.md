# Decision Pipeline and Gating Logic (v1)

Last updated: 2025-12-29  
Last verified: 2025-12-29 — matches v1 taxonomy + Tier policy.

## Objective
Define the **exact decision pipeline** the middleware will follow from inbound message → routing → optional auto-reply.

This is the “source of truth” for:
- engineering implementation (builders)
- QA test planning
- safety reviews

## Core principle
The LLM output is **advisory**.
The middleware must enforce safety and business rules in **application logic**:
- strict JSON schema validation (fail closed)
- Tier policy gates (Tier 0 override; Tier 2 requires deterministic match + verifier)
- automation kill switches

This is reinforced by the optional Wave 04 prototype harness (see `Prototype_Validation_Notes.md`), but it is a requirement regardless of any prototype.

---

---

## High-level pipeline
1) Receive inbound event from Richpanel
2) Preprocess + extract minimal features (deterministic)
3) Run Tier 0 checks (deterministic + model risk flags)
4) Run LLM classifier → `mw_decision_v1`
5) Enforce policy gates in code (Tier 0/1/2/3)
6) If Tier 2 recommended → run verifier → allow/deny
7) Execute allow-listed actions (tags, assignment routing, templates)
8) Log (PII-safe) + metrics

---

## Step-by-step with gates

### Step 1 — Inbound event normalization
Inputs:
- conversation_id
- channel
- customer message text (raw)
- message id / timestamp
- any richpanel metadata (contact id, etc.)

Actions:
- strip HTML, normalize whitespace
- remove agent signatures / quoted history where feasible
- cap length (e.g., first 4k chars) for the model input

Output:
- `normalized_text`

### Step 2 — Deterministic feature extraction
Compute:
- `has_order_number` (regex heuristics)
- `has_email` (regex)
- `has_phone` (regex)
- `has_tracking_number` (regex)
- `has_attachments` (from payload)
- `channel` (email/livechat/social/tiktok/phone)

Optional:
- `deterministic_order_link` (true/false/unknown) from Richpanel/Shopify linkage if available

Important:
- These features are passed to the model to improve decisions.
- We do **not** store raw values (e.g., the email/phone/order#) in logs by default.

### Step 3 — Tier 0 pre-checks (fast allowlist rules)
Before calling the model, run a small keyword/rule screen:
- chargeback/dispute terms
- lawsuit/lawyer terms
- explicit threats

If hit:
- skip Tier 2/3 logic
- route directly to escalation destination
- optional neutral ack template

Why:
- reduces reliance on the model for critical safety routing
- reduces chance of missing an escalation due to model error

### Step 4 — LLM classifier (structured output)
Call the model with:
- normalized_text (untrusted)
- channel + booleans
- deterministic_order_link boolean if available
- intent taxonomy + team list + tier policy
- template allowlist

Output:
- `mw_decision_v1` JSON object (schema validated)

### Step 4.5 — Canonicalize intents (multi-intent priority)
The model may propose multiple intents. Before applying tier gates, canonicalize the intent set:

- Select **one** `primary_intent`
- Select up to **two** `secondary_intents`
- Apply deterministic precedence rules from:
  - `Multi_Intent_Priority_Matrix.md`

Notes:
- If any Tier 0 intent exists, it becomes the primary intent and disables automation.
- Prefer root-cause workflows (shipping exception) over desired outcomes (refund request) when both appear.

This step ensures tier gating is applied to the **final primary intent**, not whatever the model happened to list first.

### Step 5 — Application-layer policy enforcement (hard gates)
Regardless of model output, enforce:

**Gate A — Tier 0**
If risk flags include chargeback/legal/harassment/fraud:
- force Tier 0
- destination = escalation team
- action = ACK_ONLY or ROUTE_ONLY

**Gate B — Tier 2**
Tier 2 is only possible when:
- primary intent ∈ {order_status_tracking, shipping_delay_not_shipped}
- deterministic_order_link == true
- template_id is allowlisted
Otherwise downgrade to Tier 1 or route-only.

**Gate C — Tier 3**
Tier 3 is disabled in early rollout.
If model recommends Tier 3 → downgrade to Tier 1 (intake) + route to human.

**Gate D — Always**
- auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) by default (auto-close only for whitelisted templates; see Human Handoff policy)
- never send free-form generated replies (templates only)
- template_id must exist in `Template_ID_Catalog.md` (and be enabled for the current rollout stage)

### Step 6 — Tier 2 verifier (conditional)
If Tier 2 is still eligible after gates:
- run verifier prompt with:
  - deterministic_order_link
  - proposed intent
  - normalized_text

If verifier denies:
- downgrade to Tier 1 (ask for order#) or route-only

### Step 7 — Execute allowlisted actions
Actions we execute:
- add tags (mw-intent-*, mw-routing-applied, mw-tier-*)
- (optional) trigger routing/assignment rule via tag
- send template reply when allowed

Actions we do NOT execute in early rollout:
- refunds, cancellations, address changes, reships, exchanges
- any “close ticket” or status change

### Step 8 — Logging + metrics
Log (PII-safe):
- decision object (redacted)
- policy gate outcomes (which gates changed the decision)
- latency + token usage
- template id (if sent)
- final destination team

Metrics:
- Tier distribution
- abstain/manual triage rate
- mismatch vs final human routing (proxy accuracy)
- automation send rate + customer reply rate (loop detection)

---

## Failure modes (and required behavior)
- Model timeout / refusal / invalid JSON → route-only fallback + tag `mw-model-failure`
- Missing deterministic order link for Tier 2 → Tier 1 ask-for-order-number
- Multiple intents with action requests (cancel + status) → route to human; deny Tier 2

---

## Notes for Cursor agents
Implementation should:
- validate schema strictly
- never trust model output without allowlist checks
- make gates auditable (structured “gate report” in logs)