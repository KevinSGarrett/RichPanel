# Wave 03 — Cursor Agent Tasks (Tenant Verification + Config Planning)

Last updated: 2025-12-22  
Status: **Deferred** (run later; not blocking planning)

> **Deferred:** Per owner instruction, we are holding off on these tenant/UI verification checks for now.
> The integration design includes safe fallbacks, so planning can continue.
> Run these checks before implementation / before go-live to confirm the exact Richpanel UI capabilities in your workspace.


This file is written for **Cursor builder agents**, not for you to answer from memory.

## What this is asking (plain English)
Richpanel workspaces differ a bit (plans, enabled features, UI options).  
Before we lock the final Richpanel → Middleware trigger configuration, we want a Cursor agent to do a few **quick “yes/no” checks** inside your Richpanel admin UI (and optionally 1–2 API calls).

These checks prevent the most common integration failures:
- trigger never fires because of automation ordering / “skip subsequent rules”
- webhook is unauthenticated (security risk)
- webhook payload breaks because message text includes quotes/newlines
- order automation fails because orders aren’t consistently linked to tickets

## Important: we can proceed even if checks fail
For every check below, the plan already includes a **fallback** so we are not blocked.

## How the agent should report back
Return a short markdown note with:
- ✅ / ❌ for each check
- 1–3 screenshots where relevant (redact PII)
- any “where in the UI” notes so we can document it precisely

---

## Check 1 — Can an Automation rule call an HTTP Target/webhook?
**Why:** This determines where we place our middleware trigger (Tagging Rules vs Assignment Rules).

**Agent steps (UI)**
1) Open Richpanel Admin → **Automations** (or Settings → Automations).
2) Locate the automation categories (commonly **Tagging Rules** and **Assignment Rules**).
3) Create a **test rule** (staging if you have it; otherwise a non-impacting rule in prod).
4) In the “Then/Action” dropdown, check whether an action exists like **HTTP Target** / **Webhook** / **Send to URL**.
5) Record:
   - Is HTTP Target available under **Tagging Rules**? (yes/no)
   - Is HTTP Target available under **Assignment Rules**? (yes/no)
   - Screenshot of the action dropdown.

**Fallback if Tagging Rules cannot call HTTP Target**
- Place the middleware trigger as the **first Assignment Rule** and ensure it does **not** “skip subsequent rules”.

---

## Check 2 — Can HTTP Targets include custom headers?
**Why:** We prefer authenticating inbound calls using a shared secret header (e.g., `X-Middleware-Token`).

**Agent steps (UI)**
1) Open an existing **HTTP Target** configuration or create a new one.
2) Look for a **Headers** section (or similar).
3) Attempt to add: `X-Middleware-Token: test-token`
4) Screenshot + yes/no.

**Fallback if headers are not supported**
- Put the secret token in the **request body** (e.g., `middleware_token`) or querystring and validate it in the Lambda ingress.

---

## Check 3 — Does the HTTP Target body template safely handle message text?
**Why:** If message text is injected unsafely, it can break JSON and/or create logging/PII issues.

**Agent steps (UI + test message)**
1) In the HTTP Target body template, include the available variable for the latest customer message text  
   (example placeholder: `{ticket.lastMessage.text}` — use whatever Richpanel supports in your workspace).
2) Send a test customer message containing tricky characters, e.g.:
   - quotes: `He said "hello"`
   - newlines: `line1\nline2`
3) Verify the receiving endpoint gets **valid JSON** (agent can use a request-bin style endpoint or a temporary Lambda log receiver).
4) Record yes/no and (redacted) sample payload.

**Fallback (our v1 default)**
- **Do not send message text at all.**  
  Send only `ticket_id` (and optionally `ticket_url`). Middleware fetches message content via Richpanel API.

---

## Check 4 — Order linkage coverage (Richpanel ↔ Shopify)
**Why:** Order status/tracking automation only works if orders are reliably linked to tickets.

**Agent steps (API — optional but strongly helpful)**
1) Pick 5–10 recent tickets you believe have orders attached.
2) Call: `GET /v1/order/{conversationId}`  
3) Record how often it returns:
   - linked order object (includes `orderId` / `appClientId`), vs
   - `{}` (no link)
4) For linked orders, fetch order details and confirm whether tracking fields exist.

**Fallback if linkage is inconsistent**
- Order-status automation stays **Tier 1 / Tier 2 gated**:
  - if no link → ask for order number + route to human (no sensitive disclosure)
  - if linked → include tracking details (deterministic match)

---

## Check 5 — Can we control automation rule ordering?
**Why:** Existing rules using “skip subsequent rules” can prevent the middleware trigger from firing if it’s placed below them.

**Agent steps (UI)**
1) In the automations list, try to **reorder** rules (drag/drop or priority controls).
2) Record yes/no and screenshot.

**Fallback if ordering cannot be changed**
- Create multiple inbound triggers (per channel category) and rely on **idempotency** to ensure safe behavior.

---

## Required deliverable format
Agent returns something like:

- Check 1: ✅ Tagging Rules support HTTP Target / ❌ (screenshot)
- Check 2: ✅ Headers supported / ❌ (screenshot)
- Check 3: ✅ JSON safe / ❌ (payload breaks)
- Check 4: Linked orders: 7/10 tickets; tracking populated: 6/7
- Check 5: ✅ ordering supported / ❌
