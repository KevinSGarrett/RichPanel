# Team/Tag Mapping and Drift Management

Last updated: 2025-12-21
Last verified: 2025-12-21 — Updated to v1 routing-tag strategy (`route-*`) and added drift detection plan using Richpanel list endpoints.

## Why this matters
Routing correctness depends on configuration that can drift:
- teams can be renamed/deleted
- tags can be renamed/deleted
- automation rules can be disabled/changed

If mapping drifts silently, the middleware can “route” but nothing happens in Richpanel.

---

## 1) Canonical destinations (source of truth)
We will keep a canonical list of destinations in code/config:

- Sales Team
- Backend Team
- Technical Support Team
- Phone Support Team
- TikTok Support
- Returns Admin
- LiveChat Support
- Leadership Team
- SocialMedia Team
- Email Support Team
- Chargebacks / Disputes

---

## 2) v1 mapping strategy (recommended)
### 2.1 Tag-driven routing (primary)
Middleware sets exactly one `route-*` tag per decision.
Richpanel assignment rules map the tag → Team assignment.

This means middleware does **not** need to know internal Richpanel team IDs at runtime for v1 routing.

### 2.2 Versioned mapping file (still required)
We still maintain a mapping file so:
- routing decisions are explicit and reviewable
- drift checks know what to validate
- future v2 can switch to direct team assignment if desired

Recommended format (example):

```yaml
destinations:
  sales_team:
    display_name: "Sales Team"
    route_tag: "route-sales-team"
  chargebacks_disputes:
    display_name: "Chargebacks / Disputes"
    route_tag: "route-chargebacks-disputes"
```

---

## 3) Drift detection (v1)
### 3.1 What we validate automatically
Nightly (or hourly in early rollout), run a drift check that validates:
- required Teams exist (by name)
- required Tags exist (by name)
- required Tags are not archived (if Richpanel supports archiving)

### 3.2 How to validate (API approach)
Use Richpanel API list endpoints:
- list Teams
- list Tags

Auth uses the `x-richpanel-key` header (per environment).

If API listing is unreliable in your tenant, fallback to:
- manual export snapshot weekly
- compare against the mapping file

### 3.3 Alerting
If drift detected:
- emit a high-severity alert (routing may be broken)
- optionally: fail “routing apply” actions in worker and route to a default human queue with an internal note

---

## 4) Drift prevention practices
- Prefix all middleware-managed tags with `route-` or `mw-` so they are easy to recognize.
- Restrict tag deletion permissions if possible (Support Ops only).
- Add “config review” to release checklist:
  - verify key automation rules are enabled
  - verify HTTP Target endpoint/token are current

---

## 5) Open items (confirm in your tenant)
- Can we express “tag NOT present” in automation conditions? If yes, we can prevent legacy rules from fighting middleware routing.
- Does your Richpanel tenant allow listing tags/teams via API for drift checks?

