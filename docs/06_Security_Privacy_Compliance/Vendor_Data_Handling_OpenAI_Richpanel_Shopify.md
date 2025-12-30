# Vendor Data Handling (OpenAI, Richpanel, Shopify)

Last updated: 2025-12-22

This document is a **practical checklist** for privacy/security implications of our third-party vendors.

---

## 1) OpenAI (models used for routing + FAQ decisioning)

### 1.1 Data retention and “store” behavior (important)
OpenAI platform documentation describes a **30-day** retention period for Responses API *application state* by default, and that the `store` parameter controls whether response objects are stored. It also describes that when **Zero Data Retention** is enabled for an org, `store` is treated as `false`.  
Source: OpenAI Platform Docs → “Your data”. (See references at bottom.)

**Best-suggested v1 configuration:**
- Always set `store=false` for routing/FAQ decisions.
- Do not send any unnecessary PII (see PII policy).
- Consider requesting **Zero Data Retention (ZDR)** if eligible.

### 1.2 Training usage
OpenAI’s enterprise/business privacy posture (and platform data controls) provides mechanisms so customer data is not used to train models by default for business offerings, and provides data control options.  
(Exact rules depend on your OpenAI account type; confirm in OpenAI console.)

**Best-suggested v1 requirement:**
- Use the OpenAI platform “data controls” setting consistent with your privacy requirements.
- Document the setting in the deployment checklist.

### 1.3 Encryption & access controls (vendor-side)
OpenAI’s enterprise privacy page describes encryption in transit and at rest and access controls.  
(See references.)

### 1.4 API key safety
OpenAI publishes API key safety best practices:
- keep keys server-side
- use unique keys
- rotate keys
- monitor usage

**Requirement:** middleware is the only place OpenAI keys exist (never Richpanel macros, never clients).

---

## 2) Richpanel
We use Richpanel for:
- webhook triggers (HTTP Targets)
- ticket tagging/assignment
- order linkage to Shopify (if available)

**Checklist (to confirm with your Ops/admin):**
- How are HTTP Targets authenticated (headers allowed or not)?
- Does Richpanel support IP allowlists for outbound HTTP targets?
- Is there an audit trail for automation changes?
- Key rotation process for `x-richpanel-key`

---

## 3) Shopify
Shopify is the source of truth for order status and fulfillment tracking (if we use it directly).

**Checklist:**
- Method of access (custom app / private app / access token)
- Token storage in Secrets Manager
- Least-privilege scopes for read-only order fulfillment tracking
- Rate limits and retry requirements

---

## 4) Vendor incident handling (minimum plan)
If any vendor is down or rate-limiting heavily:
- Middleware must fall back to **route-only** (no automation)
- Queue backlog should be bounded (DLQ + alerts)
- Operators must have a runbook for switching to “safe mode”

---

## References
- OpenAI Platform Docs — “Your data” (data controls, retention, `store`, ZDR)
- OpenAI Help Center — “Best Practices for API Key Safety”
- OpenAI — “Enterprise privacy”
