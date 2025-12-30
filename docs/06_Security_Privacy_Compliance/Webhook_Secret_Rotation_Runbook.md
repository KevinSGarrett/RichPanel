# Webhook Secret Rotation Runbook (No-downtime)

Last updated: 2025-12-22  
Scope: rotating the Richpanel → middleware webhook authentication secret(s)

This runbook ensures we can rotate webhook secrets **without downtime** and without accidentally breaking inbound routing.

Related:
- Webhook auth options: `Webhook_Auth_and_Request_Validation.md`
- Secrets management: `Secrets_and_Key_Management.md`
- Kill switch: `Kill_Switch_and_Safe_Mode.md`
- Incident response: `Incident_Response_Security_Runbooks.md`

---

## 1) Goals and non-goals

### Goals
- Rotate secrets safely with **overlap** (old + new valid for a short window)
- Prevent automation/routing disruption
- Provide an emergency rotation path for suspected compromise

### Non-goals
- This does not cover OpenAI or Shopify key rotation (see `Secrets_and_Key_Management.md`)

---

## 2) Secret model (recommended)

Because Richpanel tenant capabilities may vary, we support these auth transport options:
- Custom header token (preferred): `X-Middleware-Token: <token>`
- Body token (fallback): `token: "<token>"` in JSON
- URL token (fallback): `<WEBHOOK_URL>?token=<token>` (least preferred due to logging risk)

**Rotation-friendly implementation requirement:** middleware must accept **multiple active tokens**.

### Recommended storage (v1)
Store tokens in AWS Secrets Manager as JSON:

```json
{
  "active_tokens": ["token_v2", "token_v1"],
  "created_at": "2025-12-22",
  "notes": "Richpanel inbound webhook tokens"
}
```

Middleware validation:
- extract provided token (header/body/url)
- compare against `active_tokens`
- reject if not present

---

## 3) Standard rotation procedure (planned rotation)

### Step 0 — Pre-checks (5 minutes)
- [ ] Confirm current system health (no backlog, no active incidents)
- [ ] Confirm safe mode is **OFF** (unless intentionally enabled)
- [ ] Confirm you have access to update:
  - AWS Secrets Manager secret value
  - Richpanel HTTP Target config (or whichever trigger is used)

### Step 1 — Generate new token (v2)
- [ ] Generate a high-entropy token (32+ bytes random; base64/hex)
- [ ] Add it to `active_tokens` **before** removing v1

Example:
- `active_tokens`: [`token_v2`, `token_v1`]

### Step 2 — Deploy / refresh middleware secret cache
Depending on implementation:
- If middleware reads secrets at runtime with caching: wait for cache TTL
- If middleware loads secrets on cold start: deploy a no-op change or restart (as needed)

**Goal:** middleware must accept both tokens before Richpanel changes.

### Step 3 — Update Richpanel trigger to send v2
- [ ] Update HTTP Target to send `token_v2`
  - header preferred
  - body fallback if headers not supported
- [ ] Save

### Step 4 — Monitor overlap window
Monitor for 15–30 minutes:
- [ ] `auth.invalid_token_total` stays near zero
- [ ] inbound routing continues
- [ ] no increase in 4XX/5XX

### Step 5 — Remove old token (v1)
- [ ] Remove `token_v1` from `active_tokens`
- [ ] Keep an audit note (Decision Log + Change Log)

### Step 6 — Post-rotation verification
- [ ] Confirm no webhook retries/duplicates increased
- [ ] Confirm no DLQ messages increased
- [ ] Confirm dashboards stable

---

## 4) Emergency rotation (suspected compromise)

If token is suspected leaked (e.g., random traffic, invalid token spike, webhook abuse):
1) **Enable safe mode** immediately:
   - set `safe_mode=true` and/or `automation_enabled=false`
2) Rotate token using the same procedure above, but shorten overlap window
3) Add additional containment:
   - API Gateway WAF (if enabled) to block malicious IPs
   - stricter API Gateway throttling temporarily
4) After containment, investigate logs (PII-safe) and document incident

---

## 5) Rotation frequency (recommended)
- Planned rotation: every **90 days** (v1)
- Immediate rotation: anytime a secret is exposed in logs/tickets/docs

---

## 6) Documentation required (every rotation)
- [ ] Record in `docs/00_Project_Admin/Change_Log.md`
- [ ] Record in `docs/00_Project_Admin/Decision_Log.md` (if policy changes)
- [ ] Note the date/time of rotation and the owner
