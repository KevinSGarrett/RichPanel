# Template Rendering and Variables

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Define:
- the variable contract for templates (`templates/templates_v1.yaml`)
- global brand constants (`templates/brand_constants_v1.yaml`)
- formatting rules (dates, links)
- how templates are rendered safely into API payloads

This prevents common issues:
- broken JSON due to unescaped newlines/quotes
- missing variables → awkward customer messages
- leaking disallowed fields (addresses, payment details)
- drift between channels (LiveChat vs Email)

---

## Template format
**Selected:** Mustache-style templates.

Recommended:
- Mustache-compatible renderer (example: `pystache`) or equivalent.

---

## Channel selection rule
Templates may define multiple channel variants under `channels`, e.g.:
- `default`
- `livechat`
- (optional future) `email`

**Rule (v1):**
1) If a channel-specific variant exists (e.g., `livechat`), use it.
2) Otherwise use `default`.

Email uses `default` unless `email` is added later.

---

## Global variables (brand constants)
Source file: `templates/brand_constants_v1.yaml`

### Required global vars (v1)
- `support_signature`  
  Default if missing: `"Customer Support"`

### Optional global vars
- `support_hours_text`
- policy/help URLs (all blank by default in v1)

**Important:** These are not secrets. Do not store credentials here.

---

## Placeholder format (Mustache)
### Simple variables
- `{{order_id}}`
- `{{order_status}}`

### Optional blocks
If the variable is missing/empty, the entire block is omitted:
- `{{#tracking_url}}Tracking: {{tracking_url}}{{/tracking_url}}`

### Rules
- Do not include customer message text inside templates.
- Do not include sensitive fields such as shipping address, payment details, full phone/email unless required for verification and permitted by policy.
- Prefer links only when they are correct and stable; policy links are disabled by default in v1.

---

## Safe rendering rules (must-follow)
1) **Fail closed on missing required vars**  
   - If a template’s `required_vars` are missing, downgrade to a safe Tier 1 intake template or route-only.
2) **Escape for transport**  
   - Templates contain newlines; escape appropriately for the API payload you’re sending.
3) **Drop unknown/extra vars**  
   - Avoid “accidental disclosure” by only passing allowlisted variables.
4) **Never let the model render copy**  
   - Model outputs only: `template_id`, `intent`, `confidence`, `routing` metadata.

---

## Variable allowlist guidance (v1)
Allowed variables typically include:
- `first_name` (optional)
- `order_id`
- `order_status`
- `fulfillment_status` (optional)
- `tracking_url` (Tier 2 only)
- `tracking_number` (Tier 2 only)
- `tracking_company` (optional)
- `status_url` (optional)

Not allowed in v1 automated replies:
- full shipping address
- payment method details
- account credentials
