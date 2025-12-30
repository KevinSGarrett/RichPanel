# Change Management

Last updated: 2025-12-22

This document defines **how changes are requested, reviewed, tested, released, and rolled back** for the Richpanel Routing + FAQ Automation middleware.

The goal is to prevent the most common failure modes in LLM + automation systems:
- silent regressions (routing accuracy drops, wrong team assignments)
- “small copy edits” causing policy violations or broken variable rendering
- untested threshold changes causing over‑automation or under‑automation
- changes made directly in production (Richpanel macros, automations) without an audit trail

---

## Scope

This change process applies to:

### A) LLM + policy artifacts (highest risk)
- intent taxonomy and labeling guide
- prompts
- output schemas
- confidence thresholds and gating rules
- Tier policies (Tier 0/Tier 1/Tier 2/Tier 3)

### B) FAQ automation artifacts
- `template_id` catalog and enablement flags
- template copy (by channel: default/email/livechat)
- template variables / rendering rules
- macro alignment plan (Richpanel macros)

### C) Integration + runtime behavior
- Richpanel trigger rules and routing tags
- outbound reply behavior
- idempotency/dedup logic
- vendor call settings (timeouts/retries)
- kill switch / safe mode behavior

---

## Change classes (and the minimum required gates)

> **Rule of thumb:** if a change can affect what customers see, how tickets are routed, or what data leaves the system, it must have an explicit gate and an explicit rollback.

| Change class | Examples | Risk | Minimum required gates |
|---|---|---:|---|
| Copy-only template change | tone tweaks, grammar fixes | Med | Template rendering check + “no policy leak” review + staging smoke pack |
| Template variables change | adding `{tracking_url}` | High | Rendering tests + Tier policy verification + staging smoke pack |
| Template enable/disable | turning on/off a template_id | Med | Go/No-Go checklist + monitor after enable |
| Threshold change | raising order-status threshold | High | Golden set run + Tier 0 FN=0 gate + staged rollout |
| Prompt change | new instructions, new examples | High | Golden set regression + adversarial suite + staged rollout |
| Taxonomy change | new intent, rename intent | High | Labeling SOP + eval run + update routing table + training update |
| Schema change | new fields, renamed fields | High | Contract tests + backwards compatibility plan + canary |
| Integration change | webhook/auth method | High | Contract tests + replay/idempotency tests + rollback |
| Vendor model change | model version update | High | Model update policy gates + cost/latency validation |

---

## Roles and approvals (v1 recommended)

This is the **best‑suggested default governance** for early rollout.

- **Support Ops Owner** (Accountable): customer-facing copy, macro alignment, routing taxonomy “business meaning”
- **Engineering Owner** (Accountable): pipeline logic, gating, rollouts, reliability
- **Security/Privacy Reviewer** (Consulted): anything affecting data exposure, logging, auth
- **Leadership** (Informed):重大 changes, policy changes, notable regressions

> The RACI breakdown is detailed in `Artifact_Ownership_RACI.md`.

---

## Standard change workflow (default path)

### Step 1 — Create a change request ticket
Minimum ticket fields:
- **Change type** (from the table above)
- **Motivation** (what problem we’re solving)
- **Scope** (what intents/templates/teams are affected)
- **Risk assessment** (what could go wrong)
- **Rollout plan** (dev → staging → prod; % rollout if applicable)
- **Rollback plan** (exact lever to revert safely)
- **Owner** (single accountable person)

### Step 2 — Make the change in source of truth
- Prompts/templates/schemas/policies must be updated in the repo.
- Avoid direct production edits in Richpanel as a “source of truth.”
  - If a Richpanel macro must be edited, reflect the same change in `templates_v1.yaml` (or disable the macro and use middleware rendering).

### Step 3 — Required validations
Minimum validations (by class):
- **Schema validation** (always, if structured output touched)
- **Template render validation** (always, if templates touched)
- **Golden set regression** (if prompt/threshold/taxonomy/model changed)
- **Adversarial suite** (if prompt/policy changed)
- **Smoke test pack** in staging (always for customer-facing changes)

### Step 4 — Review and approvals
- Peer review required for all changes affecting prod behavior.
- Security review required for any change touching:
  - webhook auth, secrets, logs, PII handling, vendor payloads

### Step 5 — Release with progressive enablement
Default safe rollout sequence:
1. Deploy code/config changes with **automation disabled** (route-only)
2. Enable **Tier 1 safe-assist** for a limited template set
3. Enable **Tier 2 verified** order status/tracking (only when deterministic match gates pass)

### Step 6 — Post-release monitoring
For the first 24 hours after enabling new automation:
- watch misroute rate, override rate, and automation rate
- watch Tier 0 false negatives and any PII risk indicators
- be ready to toggle safe mode / disable automation

---

## Emergency change workflow (“fast path”)

Use only when there is customer harm or security risk.

Allowed emergency actions:
- set `automation_enabled=false`
- set `safe_mode=true`
- disable a specific template_id
- revert to previous model/prompt version

Emergency workflow:
1. Mitigate immediately (kill switch / safe mode).
2. Open a ticket within 2 hours describing the mitigation and what was changed.
3. Within 24 hours: postmortem-lite + add a preventative control/test.

---

## Rollback playbook (must exist before every risky change)

Every high-risk change must declare **one** primary rollback lever:
- revert the commit to prior prompt/template/schema
- pin model to previous version
- disable template_id
- disable automation globally
- route-only safe mode

If unsure, choose the safest rollback:
- **disable automation** and keep routing active.

---

## Documentation requirements (non-negotiable)
For any production-impacting change, update:
- `docs/00_Project_Admin/Change_Log.md`
- `docs/00_Project_Admin/Decision_Log.md` (if thresholds/policy changes)
- relevant wave docs (to prevent drift)

