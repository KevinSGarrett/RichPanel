# Kill Switch and Safe Mode (Security + Safety Control)

Last updated: 2025-12-22

This document defines the **emergency controls** that prevent the middleware from causing customer harm or data leakage.

> **Core requirement:** We must be able to disable automation **in minutes**, without requiring code changes.

---

## 1) Definitions

- **Routing:** applying tags / department mapping / assignment for a ticket.
- **Automation:** sending any **outbound message** to a customer automatically (FAQ replies).
- **Safe mode:** a degraded mode where we keep the system operational, but **reduce risk**:
  - route-only
  - no automation
  - stricter limits on vendor calls

---

## 2) Required kill switches (v1)

### 2.1 Global automation kill switch (required)
**Flag:** `automation_enabled`  
- `true` → automation is allowed (subject to policy gates)
- `false` → **no auto-replies** under any circumstance

**Behavior when OFF:**
- still route/tag/assign
- still log decisions (PII-safe)
- never send messages to customers
- never attempt order disclosure

### 2.2 Channel scope switch (required)
**Flag:** `automation_enabled_channels` (set of channel types)

v1 default (from Wave 05 decisions):
- enabled: `livechat`, `email`
- disabled: `social`, `tiktok`, `phone`

### 2.3 Template-level enablement (required)
**Flags:** `template_enabled.<template_id>`  
Allows disabling a single template without turning off all automation.

Use cases:
- a single FAQ template is wrong or confusing
- a template triggers many “that’s wrong” replies

### 2.4 Safe mode (required)
**Flag:** `safe_mode`  
When `true`, we assume vendor instability or an incident.

Safe mode behavior (v1):
- force `automation_enabled = false` (route-only)
- cap concurrency lower (protect downstream APIs)
- shorten worker timeouts
- disable optional enrichment calls
- increase logging/metrics sampling (PII-safe) to aid investigation

---

## 3) Where the flags live (recommended v1 implementation)

We choose a solution that is **fast to change**, requires **no redeploy**, and is secured by IAM.

### Recommended v1: SSM Parameter Store (Standard parameters)
- Store flags under a prefix, for example:
  - `/richpanel-mw/prod/automation_enabled`
  - `/richpanel-mw/prod/safe_mode`
  - `/richpanel-mw/prod/automation_enabled_channels`
- Worker lambda reads flags at runtime with a short in-memory cache (e.g., 30–60s TTL).

Pros:
- simple
- no new moving parts
- can be changed in console/CLI quickly

Alternative (later):
- AWS AppConfig for structured feature flagging and gradual rollouts.

> Security note: only a small group should have permission to modify these parameters.

---

## 4) Automatic safe-mode triggers (optional v1)

Automatic safe mode can be risky (false positives).  
For v1 we prefer **manual** toggling, but we define recommended triggers:

### Recommended triggers for manual action
- Spike in “wrong auto-reply” signals (customer says “wrong”, “not my order”, etc.)
- High OpenAI failures (>= 5% for 10 minutes) or latency blowups
- Richpanel 429/rate-limit storms
- Unexpected cost spike (budget alarm)
- Suspected webhook abuse (WAF rate-limit events, suspicious IPs)

### Optional (later) auto-switch
If implemented later, it must:
- require 2 triggers (e.g., error rate + customer complaint)
- automatically revert only after a cool-down + manual approval

---

## 5) Operational runbook (v1)

### 5.1 Emergency: stop all automation
1) Set `/.../automation_enabled = false`
2) Optionally set `/.../safe_mode = true`
3) Verify within 2 minutes:
   - automation events drop to 0
   - routing continues
   - no outbound messages are being sent

### 5.2 Rollback / resume automation
1) Set `/.../safe_mode = false`
2) Enable specific template(s) first:
   - `template_enabled.order_status_tracking_verified = true`
3) Then set `/.../automation_enabled = true`
4) Monitor:
   - customer corrections (“that’s wrong”)
   - Tier 0 misroutes (must remain 0)
   - latency and rate limits

---

## 6) Required logging & metrics

We must log:
- `safe_mode` (true/false)
- `automation_enabled` (true/false)
- `automation_action_taken` (true/false)
- `template_id` (if applicable)

We must alert on:
- automation actions occurring when `automation_enabled=false` (should be impossible)
- DLQ > 0
- webhook auth failures spike (potential attack)

---

## 7) Test cases (required)

- [ ] With `automation_enabled=false`, a message that would normally trigger order status **does not** auto-reply.
- [ ] With `safe_mode=true`, worker runs route-only and exits cleanly.
- [ ] With a single `template_enabled.*=false`, only that template is blocked.
- [ ] Flags changes take effect without redeploy (within cache TTL).

